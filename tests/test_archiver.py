import os
from pathlib import Path
from common_lib.archiver import FileArchiver


def test_archive_file_success(tmp_path):
    src = tmp_path / "input.txt"
    src.write_text("hello")

    dest = tmp_path / "archive"

    with FileArchiver(str(src), str(dest)) as archiver:
        result = archiver.archive_file

    assert result is None
    today_folder = dest / Path(result or ".").parent.name  # folder by date
    assert list(dest.iterdir())  # folder created


def test_archive_file_not_exist(tmp_path):
    src = tmp_path / "notfound.txt"
    dest = tmp_path / "out"

    with FileArchiver(str(src), str(dest)) as archiver:
        result = archiver.archive_file

    assert "does not exist" in result


def test_archive_folder_success(tmp_path):
    src = tmp_path / "input.txt"
    src.write_text("hello")

    dest = tmp_path / "arch"

    with FileArchiver(str(src), str(dest)) as archiver:
        result = archiver.archive_folder

    assert result is None
    assert (dest / "input.txt").exists()


def test_archive_name_conflict(tmp_path):
    # first file
    src1 = tmp_path / "file.txt"
    src1.write_text("a")

    dest = tmp_path / "store"

    with FileArchiver(str(src1), str(dest)) as archiver:
        archiver.archive_folder

    # second file with same name
    src2 = tmp_path / "file.txt"
    src2.write_text("b")

    with FileArchiver(str(src2), str(dest)) as archiver:
        archiver.archive_folder

    assert (dest / "file.txt").exists()
    assert (dest / "file_1.txt").exists()