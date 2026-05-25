from pathlib import Path
import shutil
import sys
import zipfile

import py7zr
import requests
from tqdm import tqdm


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


BASE_DIR = get_base_dir()
DESTINATION = BASE_DIR / "MKW_Toolkit_Portable"
TOOLS_URL = "https://raw.githubusercontent.com/Artcas2/MKModKiit/refs/heads/main/files/tools.json"


def load_tools() -> dict:
    try:
        response = requests.get(TOOLS_URL, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Erreur lors de la récupération des outils : {e}")
        return {}


TOOLS = load_tools()


def download_file(url: str, file_path: Path) -> bool:
    print(f"Téléchargement de {url}...")
    try:
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        total_size = int(response.headers.get("Content-Length", 0))

        with tqdm(desc="Progression ", total=total_size, leave=False, unit="o",
                  unit_scale=True, unit_divisor=1024) as bar:
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=131072):
                    if chunk:
                        f.write(chunk)
                        bar.update(len(chunk))

        print("Téléchargement terminé.")
        return True
    except Exception as e:
        print(f"Erreur lors du téléchargement : {e}")
        return False


def extract_zip(zip_path: Path, extract_to: Path) -> bool:
    print(f"Extraction de {zip_path}...")
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_to)

        print("Extraction terminée.")
        return True
    except Exception as e:
        print(f"Erreur lors de l'extraction : {e}")
        return False


def extract_7z(file_path: Path, extract_to: Path) -> bool:
    print(f"Extraction de {file_path}...")
    try:
        with py7zr.SevenZipFile(file_path, mode="r") as zf:
            zf.extractall(path=extract_to)

        print("Extraction terminée.")
        return True
    except Exception as e:
        print(f"Erreur lors de l'extraction : {e}")
        return False


def extract_sfx(exe_path: Path, extract_to: Path) -> bool:
    print(f"Extraction de {exe_path}...")

    temp_7z = exe_path.with_suffix(".7z")
    sig = b"7z\xBC\xAF\x27\x1C"
    chunk_size = 65536

    try:
        offset = -1

        with open(exe_path, "rb") as f:
            while True:
                current_pos = f.tell()
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                idx = chunk.find(sig)
                if idx != -1:
                    offset = current_pos + idx
                    break
                if len(chunk) == chunk_size:
                    f.seek(f.tell() - len(sig))

        if offset == -1:
            raise ValueError("Aucune archive 7z trouvée dans l'exécutable.")

        with open(exe_path, "rb") as f_in, open(temp_7z, "wb") as f_out:
            f_in.seek(offset)
            shutil.copyfileobj(f_in, f_out)

        return extract_7z(temp_7z, extract_to)
    except Exception as e:
        print(f"Erreur lors de l'extraction : {e}")
        return False
    finally:
        if temp_7z.exists():
            temp_7z.unlink()


def main() -> None:
    DESTINATION.mkdir(parents=True, exist_ok=True)
    print(f"Dossier de destination : {DESTINATION}")

    for tool_name, info in TOOLS.items():
        url = info["url"]
        filename = url.split("/")[-1]
        file_path = DESTINATION / filename
        extract_path = DESTINATION / info.get("extract_path", ".")

        print(f"\nTraitement de {tool_name}...")
        extract_path.mkdir(parents=True, exist_ok=True)

        if not download_file(url, file_path):
            continue

        if info.get("extract", False):
            ext = file_path.suffix.lower()
            success = False

            if ext == ".zip":
                success = extract_zip(file_path, extract_path)
            elif ext == ".7z":
                success = extract_7z(file_path, extract_path)
            elif ext == ".exe":
                success = extract_sfx(file_path, extract_path)

            if success:
                try:
                    file_path.unlink()
                except Exception as e:
                    print(f"Impossible de supprimer {filename} : {e}")

        if tool_name == "Wiimms SZS Tools":
            try:
                extract_path = next(extract_path.glob("szs*"))
                for file_path in extract_path.glob("*install*"):
                    if file_path.is_file():
                        file_path.unlink()
            except Exception:
                pass
        elif tool_name == "Dolphin":
            try:
                (extract_path / "Dolphin-x64" / "portable.txt").touch()
            except Exception:
                pass

    print("\nInstallation terminée.")
    print(f"Dossier : {DESTINATION}")


if __name__ == "__main__":
    main()
