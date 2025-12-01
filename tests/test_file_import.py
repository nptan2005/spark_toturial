# tests/test_file_import.py

import os

import pandas as pd
from openpyxl import Workbook

from common_lib.importer.models import import_configuration
from common_lib.importer.importer import FileImport


def test_file_import_acq_bank_benefit(tmp_path):
    """
    Kiểm tra:
    - Đọc Excel theo template ACQ_BANK_BENEFIT
    - Áp dụng start_row, start_col, end_row/end_col
    - Áp dụng column_mapping -> header cuối cùng là tên cột DB (upper)
    """

    template_name = "ACQ_BANK_BENEFIT"
    tmpl = import_configuration.import_template[template_name]

    # 1) Tạo file Excel giả lập theo template
    xlsx_path = tmp_path / "acq_bank_benefit.xlsx"

    wb = Workbook()
    ws = wb.active

    # Số cột thực tế trong sheet:
    # vì start_col = 2 -> pandas sẽ đọc từ col 2 đến max_col
    # nên tạo tổng cộng len(header) + 1 cột để đảm bảo số cột đọc = len(header)
    num_cols = len(tmpl.header) + 1

    # Row 1,2: có thể coi là header / metadata => template.start_row=3 nên sẽ bỏ qua
    ws.append([f"dummy_{i}" for i in range(1, num_cols + 1)])
    ws.append([f"dummy2_{i}" for i in range(1, num_cols + 1)])

    # Row 3,4: dữ liệu thật (được đọc theo start_row=3)
    data_row_1 = list(range(1, num_cols + 1))
    data_row_2 = list(range(100, 100 + num_cols))
    ws.append(data_row_1)
    ws.append(data_row_2)

    wb.save(xlsx_path)

    # 2) Gọi FileImport để đọc
    importer = FileImport(file_name=str(xlsx_path), template_name=template_name)
    df = importer.read_file_to_df()

    # 3) Assert kết quả
    assert not df.empty, "DataFrame sau khi import không được rỗng"
    # số cột sau khi mapping phải bằng số header trong config
    assert df.shape[1] == len(tmpl.header)

    # header sau khi mapping + upper: mapping ('Bank Name' -> 'Bank_Name') -> 'BANK_NAME'
    expected_cols = [
        "BANK_NAME",
        "ACQ_BANK_CODE",
        "TAX_CODE",
        "ADDRESS",
        "CLEARING_BRANCH_CODE",
    ]
    for col in expected_cols:
        assert col in df.columns, f"Thiếu cột {col} trong DataFrame"

    # kiểm tra số dòng đúng (2 dòng dữ liệu)
    assert df.shape[0] == 2