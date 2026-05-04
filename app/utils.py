"""
Compatibility façade for report helpers.

Most report-related logic was moved to `app.reports.services`. Keep this
module as a thin compatibility layer so existing imports from
`app.utils` keep working.
"""
from app.reports.services import (
    get_path_data,
    get_reports_list,
    get_report,
    add_report_to_list,
    delete_report,
    process_and_save_report,
    get_student_data_from_db,
    get_all_academic_periods,
)

__all__ = [
    'get_path_data',
    'get_reports_list',
    'get_report',
    'add_report_to_list',
    'delete_report',
    'process_and_save_report',
    'get_student_data_from_db',
    'get_all_academic_periods',
]