"""
FAHR MCP Server — All tools with hardcoded realistic dummy data.
Replace the MOCK_* dicts with real Bayanati API calls when ready.

Run:
    pip install fastmcp
    python fahr_mcp_server.py
"""

from fastmcp import FastMCP
from datetime import datetime, timezone
from typing import Optional
import random

mcp = FastMCP("FAHR HR Tools")

# ─────────────────────────────────────────────────────────────────────────────
# MOCK DATA — swap each block with a real API call later
# ─────────────────────────────────────────────────────────────────────────────

MOCK_EMPLOYEES = {
    "204319": {
        "person_id": 204319,
        "full_name": "Mohammed Ali Al Mansoori",
        "first_name": "Mohammed",
        "last_name": "Al Mansoori",
        "email": "m.almansoori@fahr.gov.ae",
        "mobile": "+971501234567",
        "role": "employee",
        "grade": "G8",
        "job_title": "Senior Policy Analyst",
        "department": "Human Resources Policy",
        "ministry": "Ministry of Human Resources",
        "ministry_code": "MOHR",
        "manager_id": 301001,
        "manager_name": "Ahmed Khalid Al Hashimi",
        "location": "Abu Dhabi — FAHR HQ",
        "nationality": "UAE",
        "gender": "Male",
        "date_of_birth": "1985-06-15",
        "appointment_date": "2015-08-01",
        "emirates_id": "784-1985-1234567-1",
        "language": "ar",
    },
    "204320": {
        "person_id": 204320,
        "full_name": "Sara Khalid Al Zaabi",
        "first_name": "Sara",
        "last_name": "Al Zaabi",
        "email": "s.alzaabi@fahr.gov.ae",
        "mobile": "+971507654321",
        "role": "manager",
        "grade": "G10",
        "job_title": "HR Director",
        "department": "Talent Management",
        "ministry": "Ministry of Human Resources",
        "ministry_code": "MOHR",
        "manager_id": 301002,
        "manager_name": "Dr. Fatima Al Nuaimi",
        "location": "Dubai — FAHR Branch",
        "nationality": "UAE",
        "gender": "Female",
        "date_of_birth": "1980-03-22",
        "appointment_date": "2010-01-15",
        "emirates_id": "784-1980-7654321-2",
        "language": "en",
    },
    "204321": {
        "person_id": 204321,
        "full_name": "Omar Yusuf Al Rashidi",
        "first_name": "Omar",
        "last_name": "Al Rashidi",
        "email": "o.alrashidi@fahr.gov.ae",
        "mobile": "+971509876543",
        "role": "employee",
        "grade": "G6",
        "job_title": "HR Officer",
        "department": "Recruitment & Selection",
        "ministry": "Ministry of Human Resources",
        "ministry_code": "MOHR",
        "manager_id": 204320,
        "manager_name": "Sara Khalid Al Zaabi",
        "location": "Abu Dhabi — FAHR HQ",
        "nationality": "UAE",
        "gender": "Male",
        "date_of_birth": "1992-11-10",
        "appointment_date": "2019-04-01",
        "emirates_id": "784-1992-9876543-3",
        "language": "en",
    },
}

MOCK_LEAVE_BALANCES = {
    "204319": [
        {"leave_type": "Annual Leave",        "leave_type_ar": "إجازة سنوية",     "balance_days": 18, "used_days": 12, "total_entitlement": 30},
        {"leave_type": "Sick Leave",           "leave_type_ar": "إجازة مرضية",     "balance_days": 45, "used_days": 5,  "total_entitlement": 60},
        {"leave_type": "Emergency Leave",      "leave_type_ar": "إجازة طارئة",     "balance_days": 3,  "used_days": 2,  "total_entitlement": 5},
        {"leave_type": "Study Leave",          "leave_type_ar": "إجازة دراسية",    "balance_days": 10, "used_days": 0,  "total_entitlement": 10},
        {"leave_type": "Hajj Leave",           "leave_type_ar": "إجازة الحج",      "balance_days": 30, "used_days": 0,  "total_entitlement": 30},
        {"leave_type": "Compassionate Leave",  "leave_type_ar": "إجازة وفاة",      "balance_days": 5,  "used_days": 0,  "total_entitlement": 5},
        {"leave_type": "Maternity Leave",      "leave_type_ar": "إجازة أمومة",     "balance_days": 0,  "used_days": 0,  "total_entitlement": 0},
        {"leave_type": "National Service",     "leave_type_ar": "الخدمة الوطنية",  "balance_days": 0,  "used_days": 0,  "total_entitlement": 0},
        {"leave_type": "Unpaid Leave",         "leave_type_ar": "إجازة بدون راتب", "balance_days": 90, "used_days": 0,  "total_entitlement": 90},
        {"leave_type": "Work From Home",       "leave_type_ar": "عمل عن بعد",      "balance_days": 8,  "used_days": 2,  "total_entitlement": 10},
    ],
    "204320": [
        {"leave_type": "Annual Leave",        "leave_type_ar": "إجازة سنوية",     "balance_days": 22, "used_days": 8,  "total_entitlement": 30},
        {"leave_type": "Sick Leave",           "leave_type_ar": "إجازة مرضية",     "balance_days": 60, "used_days": 0,  "total_entitlement": 60},
        {"leave_type": "Emergency Leave",      "leave_type_ar": "إجازة طارئة",     "balance_days": 5,  "used_days": 0,  "total_entitlement": 5},
        {"leave_type": "Study Leave",          "leave_type_ar": "إجازة دراسية",    "balance_days": 15, "used_days": 0,  "total_entitlement": 15},
        {"leave_type": "Hajj Leave",           "leave_type_ar": "إجازة الحج",      "balance_days": 30, "used_days": 0,  "total_entitlement": 30},
        {"leave_type": "Compassionate Leave",  "leave_type_ar": "إجازة وفاة",      "balance_days": 5,  "used_days": 0,  "total_entitlement": 5},
        {"leave_type": "Maternity Leave",      "leave_type_ar": "إجازة أمومة",     "balance_days": 90, "used_days": 0,  "total_entitlement": 90},
        {"leave_type": "Work From Home",       "leave_type_ar": "عمل عن بعد",      "balance_days": 6,  "used_days": 4,  "total_entitlement": 10},
        {"leave_type": "Unpaid Leave",         "leave_type_ar": "إجازة بدون راتب", "balance_days": 90, "used_days": 0,  "total_entitlement": 90},
        {"leave_type": "Paternity Leave",      "leave_type_ar": "إجازة الأبوة",    "balance_days": 0,  "used_days": 0,  "total_entitlement": 0},
    ],
    "204321": [
        {"leave_type": "Annual Leave",        "leave_type_ar": "إجازة سنوية",     "balance_days": 25, "used_days": 5,  "total_entitlement": 30},
        {"leave_type": "Sick Leave",           "leave_type_ar": "إجازة مرضية",     "balance_days": 58, "used_days": 2,  "total_entitlement": 60},
        {"leave_type": "Emergency Leave",      "leave_type_ar": "إجازة طارئة",     "balance_days": 5,  "used_days": 0,  "total_entitlement": 5},
        {"leave_type": "Study Leave",          "leave_type_ar": "إجازة دراسية",    "balance_days": 10, "used_days": 0,  "total_entitlement": 10},
        {"leave_type": "Hajj Leave",           "leave_type_ar": "إجازة الحج",      "balance_days": 30, "used_days": 0,  "total_entitlement": 30},
        {"leave_type": "Compassionate Leave",  "leave_type_ar": "إجازة وفاة",      "balance_days": 5,  "used_days": 0,  "total_entitlement": 5},
        {"leave_type": "Paternity Leave",      "leave_type_ar": "إجازة الأبوة",    "balance_days": 15, "used_days": 0,  "total_entitlement": 15},
        {"leave_type": "Work From Home",       "leave_type_ar": "عمل عن بعد",      "balance_days": 9,  "used_days": 1,  "total_entitlement": 10},
        {"leave_type": "Unpaid Leave",         "leave_type_ar": "إجازة بدون راتب", "balance_days": 90, "used_days": 0,  "total_entitlement": 90},
        {"leave_type": "National Service",     "leave_type_ar": "الخدمة الوطنية",  "balance_days": 0,  "used_days": 0,  "total_entitlement": 0},
    ],
}

MOCK_PAYSLIPS = {
    "204319": [
        {
            "period": "March 2026", "period_code": "202603",
            "basic_salary": 18500.00, "housing_allowance": 7000.00,
            "transport_allowance": 1500.00, "children_allowance": 1200.00,
            "other_allowances": 800.00, "gross_salary": 29000.00,
            "deductions": 1450.00, "net_salary": 27550.00,
            "currency": "AED", "payment_date": "2026-03-28",
            "bank": "ADCB", "iban": "AE07 0330 0000 0201 0101 101",
        },
        {
            "period": "February 2026", "period_code": "202602",
            "basic_salary": 18500.00, "housing_allowance": 7000.00,
            "transport_allowance": 1500.00, "children_allowance": 1200.00,
            "other_allowances": 800.00, "gross_salary": 29000.00,
            "deductions": 1450.00, "net_salary": 27550.00,
            "currency": "AED", "payment_date": "2026-02-26",
            "bank": "ADCB", "iban": "AE07 0330 0000 0201 0101 101",
        },
        {
            "period": "January 2026", "period_code": "202601",
            "basic_salary": 18500.00, "housing_allowance": 7000.00,
            "transport_allowance": 1500.00, "children_allowance": 1200.00,
            "other_allowances": 1800.00, "gross_salary": 30000.00,
            "deductions": 1500.00, "net_salary": 28500.00,
            "currency": "AED", "payment_date": "2026-01-29",
            "bank": "ADCB", "iban": "AE07 0330 0000 0201 0101 101",
        },
    ],
    "204320": [
        {
            "period": "March 2026", "period_code": "202603",
            "basic_salary": 28000.00, "housing_allowance": 10000.00,
            "transport_allowance": 2000.00, "children_allowance": 2400.00,
            "other_allowances": 1500.00, "gross_salary": 43900.00,
            "deductions": 2195.00, "net_salary": 41705.00,
            "currency": "AED", "payment_date": "2026-03-28",
            "bank": "FAB", "iban": "AE15 0350 0000 0000 2020 202",
        },
        {
            "period": "February 2026", "period_code": "202602",
            "basic_salary": 28000.00, "housing_allowance": 10000.00,
            "transport_allowance": 2000.00, "children_allowance": 2400.00,
            "other_allowances": 1500.00, "gross_salary": 43900.00,
            "deductions": 2195.00, "net_salary": 41705.00,
            "currency": "AED", "payment_date": "2026-02-26",
            "bank": "FAB", "iban": "AE15 0350 0000 0000 2020 202",
        },
    ],
    "204321": [
        {
            "period": "March 2026", "period_code": "202603",
            "basic_salary": 12000.00, "housing_allowance": 4500.00,
            "transport_allowance": 1000.00, "children_allowance": 0.00,
            "other_allowances": 500.00, "gross_salary": 18000.00,
            "deductions": 900.00, "net_salary": 17100.00,
            "currency": "AED", "payment_date": "2026-03-28",
            "bank": "Emirates NBD", "iban": "AE33 0260 0000 0000 3030 303",
        },
    ],
}

MOCK_ATTENDANCE = {
    "204319": [
        {"date": "2026-03-24", "day": "Monday",    "check_in": "08:02", "check_out": "17:15", "status": "Present",      "hours_worked": 9.2,  "late_minutes": 2},
        {"date": "2026-03-23", "day": "Sunday",    "check_in": "08:10", "check_out": "17:00", "status": "Present",      "hours_worked": 8.8,  "late_minutes": 10},
        {"date": "2026-03-22", "day": "Saturday",  "check_in": None,    "check_out": None,    "status": "Weekend",      "hours_worked": 0,    "late_minutes": 0},
        {"date": "2026-03-21", "day": "Friday",    "check_in": None,    "check_out": None,    "status": "Weekend",      "hours_worked": 0,    "late_minutes": 0},
        {"date": "2026-03-20", "day": "Thursday",  "check_in": "07:58", "check_out": "17:30", "status": "Present",      "hours_worked": 9.5,  "late_minutes": 0},
        {"date": "2026-03-19", "day": "Wednesday", "check_in": "08:45", "check_out": "17:00", "status": "Late",         "hours_worked": 8.3,  "late_minutes": 45},
        {"date": "2026-03-18", "day": "Tuesday",   "check_in": "08:00", "check_out": "17:00", "status": "Present",      "hours_worked": 9.0,  "late_minutes": 0},
        {"date": "2026-03-17", "day": "Monday",    "check_in": None,    "check_out": None,    "status": "Annual Leave", "hours_worked": 0,    "late_minutes": 0},
        {"date": "2026-03-16", "day": "Sunday",    "check_in": None,    "check_out": None,    "status": "Annual Leave", "hours_worked": 0,    "late_minutes": 0},
        {"date": "2026-03-15", "day": "Saturday",  "check_in": None,    "check_out": None,    "status": "Weekend",      "hours_worked": 0,    "late_minutes": 0},
    ],
    "204320": [
        {"date": "2026-03-24", "day": "Monday",    "check_in": "07:45", "check_out": "18:00", "status": "Present",  "hours_worked": 10.3, "late_minutes": 0},
        {"date": "2026-03-23", "day": "Sunday",    "check_in": "08:00", "check_out": "17:30", "status": "Present",  "hours_worked": 9.5,  "late_minutes": 0},
        {"date": "2026-03-22", "day": "Saturday",  "check_in": None,    "check_out": None,    "status": "Weekend",  "hours_worked": 0,    "late_minutes": 0},
        {"date": "2026-03-21", "day": "Friday",    "check_in": None,    "check_out": None,    "status": "Weekend",  "hours_worked": 0,    "late_minutes": 0},
        {"date": "2026-03-20", "day": "Thursday",  "check_in": "07:50", "check_out": "18:30", "status": "Present",  "hours_worked": 10.7, "late_minutes": 0},
        {"date": "2026-03-19", "day": "Wednesday", "check_in": "08:05", "check_out": "17:15", "status": "Present",  "hours_worked": 9.2,  "late_minutes": 5},
        {"date": "2026-03-18", "day": "Tuesday",   "check_in": "07:55", "check_out": "17:00", "status": "Present",  "hours_worked": 9.1,  "late_minutes": 0},
        {"date": "2026-03-17", "day": "Monday",    "check_in": "08:00", "check_out": "17:00", "status": "Present",  "hours_worked": 9.0,  "late_minutes": 0},
        {"date": "2026-03-16", "day": "Sunday",    "check_in": "08:00", "check_out": "17:00", "status": "Present",  "hours_worked": 9.0,  "late_minutes": 0},
        {"date": "2026-03-15", "day": "Saturday",  "check_in": None,    "check_out": None,    "status": "Weekend",  "hours_worked": 0,    "late_minutes": 0},
    ],
    "204321": [
        {"date": "2026-03-24", "day": "Monday",    "check_in": "08:30", "check_out": "17:00", "status": "Late",       "hours_worked": 8.5, "late_minutes": 30},
        {"date": "2026-03-23", "day": "Sunday",    "check_in": "08:05", "check_out": "17:00", "status": "Present",    "hours_worked": 8.9, "late_minutes": 5},
        {"date": "2026-03-22", "day": "Saturday",  "check_in": None,    "check_out": None,    "status": "Weekend",    "hours_worked": 0,   "late_minutes": 0},
        {"date": "2026-03-21", "day": "Friday",    "check_in": None,    "check_out": None,    "status": "Weekend",    "hours_worked": 0,   "late_minutes": 0},
        {"date": "2026-03-20", "day": "Thursday",  "check_in": "08:00", "check_out": "17:00", "status": "Present",    "hours_worked": 9.0, "late_minutes": 0},
        {"date": "2026-03-19", "day": "Wednesday", "check_in": "08:00", "check_out": "17:00", "status": "Present",    "hours_worked": 9.0, "late_minutes": 0},
        {"date": "2026-03-18", "day": "Tuesday",   "check_in": None,    "check_out": None,    "status": "Sick Leave", "hours_worked": 0,   "late_minutes": 0},
        {"date": "2026-03-17", "day": "Monday",    "check_in": None,    "check_out": None,    "status": "Sick Leave", "hours_worked": 0,   "late_minutes": 0},
        {"date": "2026-03-16", "day": "Sunday",    "check_in": "08:00", "check_out": "17:00", "status": "Present",    "hours_worked": 9.0, "late_minutes": 0},
        {"date": "2026-03-15", "day": "Saturday",  "check_in": None,    "check_out": None,    "status": "Weekend",    "hours_worked": 0,   "late_minutes": 0},
    ],
}

MOCK_PERFORMANCE = {
    "204319": {
        "appraisal_year": "2025",
        "appraisal_period": "Jan 2025 – Dec 2025",
        "overall_rating": 4.2,
        "rating_label": "Exceeds Expectations",
        "objectives": [
            {"title": "Policy Development Initiative",  "weight": 30, "score": 4.5, "status": "Achieved"},
            {"title": "Stakeholder Engagement",          "weight": 25, "score": 4.0, "status": "Achieved"},
            {"title": "Digital Transformation Project",  "weight": 20, "score": 4.8, "status": "Exceeded"},
            {"title": "Training Hours Completion",       "weight": 15, "score": 3.5, "status": "Partially Achieved"},
            {"title": "KPI Reporting Accuracy",          "weight": 10, "score": 4.0, "status": "Achieved"},
        ],
        "competencies": [
            {"name": "Leadership",      "score": 4.0},
            {"name": "Communication",   "score": 4.5},
            {"name": "Problem Solving", "score": 4.2},
            {"name": "Teamwork",        "score": 4.8},
            {"name": "Innovation",      "score": 3.9},
        ],
        "manager_comments": "Mohammed consistently delivers high-quality work and contributes positively to the team.",
        "promotion_recommended": True,
        "increment_percentage": 5.0,
    },
    "204320": {
        "appraisal_year": "2025",
        "appraisal_period": "Jan 2025 – Dec 2025",
        "overall_rating": 4.7,
        "rating_label": "Outstanding",
        "objectives": [
            {"title": "Department Restructuring Plan", "weight": 35, "score": 5.0, "status": "Exceeded"},
            {"title": "Emiratisation Target",          "weight": 25, "score": 4.5, "status": "Achieved"},
            {"title": "HR Digital System Rollout",     "weight": 20, "score": 4.8, "status": "Exceeded"},
            {"title": "Employee Satisfaction Score",   "weight": 10, "score": 4.5, "status": "Achieved"},
            {"title": "Budget Management",             "weight": 10, "score": 4.2, "status": "Achieved"},
        ],
        "competencies": [
            {"name": "Strategic Thinking", "score": 5.0},
            {"name": "Leadership",         "score": 4.8},
            {"name": "Communication",      "score": 4.7},
            {"name": "Decision Making",    "score": 4.5},
            {"name": "Innovation",         "score": 4.6},
        ],
        "manager_comments": "Sara demonstrates exceptional leadership and strategic vision consistently.",
        "promotion_recommended": False,
        "increment_percentage": 8.0,
    },
    "204321": {
        "appraisal_year": "2025",
        "appraisal_period": "Jan 2025 – Dec 2025",
        "overall_rating": 3.5,
        "rating_label": "Meets Expectations",
        "objectives": [
            {"title": "Recruitment Target Completion",   "weight": 40, "score": 3.5, "status": "Partially Achieved"},
            {"title": "Onboarding Process Improvement",  "weight": 30, "score": 3.8, "status": "Achieved"},
            {"title": "Training Coordination",           "weight": 20, "score": 3.0, "status": "Partially Achieved"},
            {"title": "Administrative Compliance",       "weight": 10, "score": 4.0, "status": "Achieved"},
        ],
        "competencies": [
            {"name": "Attention to Detail", "score": 4.0},
            {"name": "Communication",       "score": 3.5},
            {"name": "Teamwork",            "score": 3.8},
            {"name": "Initiative",          "score": 3.0},
            {"name": "Time Management",     "score": 3.2},
        ],
        "manager_comments": "Omar shows good potential and needs to improve time management and initiative.",
        "promotion_recommended": False,
        "increment_percentage": 3.0,
    },
}

MOCK_CRM_TICKETS = {
    "204319": [
        {
            "ticket_id": "CAS-09821-FAH1A2",
            "subject": "Query about annual leave encashment policy",
            "category": "HR Policy Inquiry", "status": "Open", "priority": "Medium",
            "created_date": "2026-03-10", "last_updated": "2026-03-20",
            "assigned_to": "HR Policy Team",
            "description": "Employee requesting clarification on leave encashment rules.",
            "resolution": None,
            "comments": ["Acknowledged 2026-03-10. Forwarded to HR Policy Team.", "Under review as of 2026-03-20."],
        },
        {
            "ticket_id": "CAS-08734-FAH3B4",
            "subject": "Payslip discrepancy — February 2026",
            "category": "Payroll", "status": "Closed", "priority": "High",
            "created_date": "2026-03-01", "last_updated": "2026-03-05",
            "assigned_to": "Payroll Team",
            "description": "Missing transport allowance in February payslip.",
            "resolution": "Transport allowance adjustment processed and reflected in March payslip.",
            "comments": ["Received and escalated to Payroll on 2026-03-01.", "Resolved on 2026-03-05."],
        },
        {
            "ticket_id": "CAS-07621-FAH5C6",
            "subject": "Emirates ID update request",
            "category": "HR Records", "status": "Closed", "priority": "Low",
            "created_date": "2026-01-15", "last_updated": "2026-01-22",
            "assigned_to": "Records Management",
            "description": "Employee requested update of Emirates ID in HR system.",
            "resolution": "Emirates ID updated successfully in Bayanati system.",
            "comments": [],
        },
    ],
    "204320": [
        {
            "ticket_id": "CAS-10012-FAH7D8",
            "subject": "System access request for new team member",
            "category": "IT & Access", "status": "Open", "priority": "High",
            "created_date": "2026-03-22", "last_updated": "2026-03-24",
            "assigned_to": "IT Support",
            "description": "Manager requested Bayanati access for newly joined HR Officer.",
            "resolution": None,
            "comments": ["Ticket raised on 2026-03-22. IT team notified."],
        },
        {
            "ticket_id": "CAS-09455-FAH9E0",
            "subject": "Budget approval for Q2 training program",
            "category": "Training & Development", "status": "Closed", "priority": "Medium",
            "created_date": "2026-02-10", "last_updated": "2026-02-28",
            "assigned_to": "L&D Department",
            "description": "Budget approval for Q2 training covering 12 employees.",
            "resolution": "Budget of AED 45,000 approved. Training scheduled for April 2026.",
            "comments": ["Submitted to Finance 2026-02-12.", "Approved 2026-02-28."],
        },
    ],
    "204321": [
        {
            "ticket_id": "CAS-09990-FAH2F3",
            "subject": "Leave request approval — sick leave March 17-18",
            "category": "Leave Management", "status": "Closed", "priority": "Medium",
            "created_date": "2026-03-18", "last_updated": "2026-03-19",
            "assigned_to": "Direct Manager",
            "description": "Sick leave for March 17-18 2026 with medical certificate.",
            "resolution": "Leave approved by Sara Al Zaabi on 2026-03-19.",
            "comments": ["Sick leave submitted with medical certificate.", "Approved by manager."],
        },
    ],
}

MOCK_PENDING_LEAVE_REQUESTS = {
    "204319": [
        {
            "request_id": "LR-2026-04471",
            "leave_type": "Annual Leave",
            "start_date": "2026-04-05", "end_date": "2026-04-10",
            "days_requested": 5, "reason": "Family vacation",
            "status": "Pending Manager Approval",
            "submitted_date": "2026-03-20",
            "approver": "Ahmed Khalid Al Hashimi",
        }
    ],
    "204320": [],
    "204321": [],
}

MOCK_TEAM_MEMBERS = {
    "204320": [
        {"person_id": 204321, "name": "Omar Yusuf Al Rashidi",    "job_title": "HR Officer",             "attendance_today": "Late",    "leave_status": "Available"},
        {"person_id": 204322, "name": "Layla Hassan Al Suwaidi",  "job_title": "Recruitment Specialist",  "attendance_today": "Present", "leave_status": "Available"},
        {"person_id": 204323, "name": "Khalid Saeed Al Bloushi",  "job_title": "Training Coordinator",    "attendance_today": "Present", "leave_status": "Available"},
        {"person_id": 204324, "name": "Noor Ahmad Al Hammadi",    "job_title": "HR Analyst",              "attendance_today": "Absent",  "leave_status": "Annual Leave"},
        {"person_id": 204325, "name": "Tariq Majid Al Falasi",    "job_title": "HR Officer",              "attendance_today": "Present", "leave_status": "Available"},
        {"person_id": 204326, "name": "Mariam Juma Al Qubaisi",   "job_title": "Admin Coordinator",       "attendance_today": "Present", "leave_status": "Available"},
        {"person_id": 204327, "name": "Saeed Rashed Al Mazrouei", "job_title": "Recruitment Officer",     "attendance_today": "Present", "leave_status": "Available"},
        {"person_id": 204328, "name": "Hessa Obaid Al Ketbi",     "job_title": "HR Specialist",           "attendance_today": "Late",    "leave_status": "Available"},
        {"person_id": 204329, "name": "Yousef Hamad Al Nuaimi",   "job_title": "Training Officer",        "attendance_today": "Present", "leave_status": "Available"},
        {"person_id": 204330, "name": "Fatima Ali Al Mheiri",     "job_title": "HR Data Analyst",         "attendance_today": "Present", "leave_status": "Available"},
    ]
}

MOCK_NOTIFICATIONS = {
    "204319": [
        {"id": "N001", "title": "Leave Request Pending",          "body": "Your annual leave request LR-2026-04471 is awaiting manager approval.",       "date": "2026-03-20", "read": False, "type": "Leave"},
        {"id": "N002", "title": "Payslip Available",              "body": "Your March 2026 payslip is now available. Net salary: AED 27,550.",            "date": "2026-03-28", "read": False, "type": "Payroll"},
        {"id": "N003", "title": "Performance Appraisal Complete", "body": "Your 2025 annual appraisal has been finalised. Rating: Exceeds Expectations.", "date": "2026-03-15", "read": True,  "type": "Performance"},
        {"id": "N004", "title": "Training Reminder",              "body": "Digital Governance training on 2026-04-02. Please confirm attendance.",        "date": "2026-03-18", "read": True,  "type": "Training"},
        {"id": "N005", "title": "Public Holiday Notice",          "body": "UAE National Commemoration Day observed on 1st December 2026.",                "date": "2026-03-01", "read": True,  "type": "General"},
        {"id": "N006", "title": "Policy Update",                  "body": "Updated Remote Work Policy effective 1st April 2026. Please review.",          "date": "2026-03-10", "read": False, "type": "Policy"},
        {"id": "N007", "title": "EID Al Fitr Holiday",            "body": "Eid Al Fitr holiday: 30 Mar – 2 Apr 2026.",                                    "date": "2026-03-05", "read": True,  "type": "General"},
        {"id": "N008", "title": "CIT Ticket Updated",             "body": "Your ticket CAS-09821-FAH1A2 has been updated.",                               "date": "2026-03-20", "read": False, "type": "CRM"},
        {"id": "N009", "title": "Overtime Logged",                "body": "4.5 hours of overtime recorded for week of 16-20 March 2026.",                 "date": "2026-03-21", "read": True,  "type": "Attendance"},
        {"id": "N010", "title": "Profile Incomplete",             "body": "Your Bayanati profile is 85% complete. Please update your qualifications.",    "date": "2026-02-28", "read": True,  "type": "Profile"},
    ],
    "204320": [
        {"id": "N101", "title": "Leave Request — Team Member",  "body": "Omar Al Rashidi submitted sick leave for Mar 17-18. Action required.",   "date": "2026-03-18", "read": False, "type": "Leave"},
        {"id": "N102", "title": "Payslip Available",            "body": "Your March 2026 payslip is available. Net salary: AED 41,705.",          "date": "2026-03-28", "read": False, "type": "Payroll"},
        {"id": "N103", "title": "IT Access Ticket Open",        "body": "Ticket CAS-10012-FAH7D8 for new joiner access is pending IT action.",    "date": "2026-03-22", "read": True,  "type": "CRM"},
        {"id": "N104", "title": "Q2 Training Budget Approved",  "body": "AED 45,000 approved for Q2 training. Coordinate with L&D to schedule.", "date": "2026-02-28", "read": True,  "type": "Training"},
        {"id": "N105", "title": "Team Attendance Alert",        "body": "2 team members marked late today (24 Mar). Review attendance report.",   "date": "2026-03-24", "read": False, "type": "Attendance"},
    ],
    "204321": [
        {"id": "N201", "title": "Sick Leave Approved",         "body": "Your sick leave for 17-18 March 2026 has been approved.",              "date": "2026-03-19", "read": False, "type": "Leave"},
        {"id": "N202", "title": "Payslip Available",           "body": "Your March 2026 payslip is available. Net salary: AED 17,100.",        "date": "2026-03-28", "read": False, "type": "Payroll"},
        {"id": "N203", "title": "Late Arrival Recorded",       "body": "Late arrival recorded on 24 March 2026 (08:30). 30 minutes late.",     "date": "2026-03-24", "read": False, "type": "Attendance"},
        {"id": "N204", "title": "Performance Review Scheduled","body": "Mid-year check-in scheduled for April 15 with Sara Al Zaabi.",        "date": "2026-03-20", "read": True,  "type": "Performance"},
        {"id": "N205", "title": "Training Mandatory",          "body": "Mandatory Ethics & Compliance training due by 30 April 2026.",         "date": "2026-03-15", "read": True,  "type": "Training"},
    ],
}

MOCK_JOB_CARD = {
    "204319": {
        "job_code": "HR-POL-G8-001", "job_title": "Senior Policy Analyst",
        "job_family": "Policy & Legislation", "grade": "G8", "step": 3,
        "department": "Human Resources Policy", "division": "Policy Research & Development",
        "section": "Federal HR Policy", "reporting_to": "HR Policy Manager",
        "work_location": "FAHR HQ — Abu Dhabi", "employment_type": "Permanent",
        "contract_type": "Full-Time", "working_hours": "7.5 hours/day — Sunday to Thursday",
        "probation_end_date": "2015-12-31", "confirmation_date": "2016-01-01",
        "years_of_service": 10,
        "qualifications_required": ["Bachelor's in Public Administration or HR", "Master's preferred"],
        "key_responsibilities": [
            "Develop and review federal HR policies",
            "Conduct benchmarking studies with international HR frameworks",
            "Prepare policy briefs for senior management",
            "Coordinate with government entities on policy implementation",
            "Monitor compliance with UAE labor legislation",
        ],
    },
    "204320": {
        "job_code": "HR-MGR-G10-002", "job_title": "HR Director",
        "job_family": "HR Leadership", "grade": "G10", "step": 5,
        "department": "Talent Management", "division": "Strategic HR",
        "section": "Talent Acquisition & Development", "reporting_to": "Assistant Undersecretary — HR",
        "work_location": "FAHR Dubai Branch", "employment_type": "Permanent",
        "contract_type": "Full-Time", "working_hours": "7.5 hours/day — Sunday to Thursday",
        "probation_end_date": "2010-06-30", "confirmation_date": "2010-07-01",
        "years_of_service": 16,
        "qualifications_required": ["Master's in HR Management or MBA", "CIPD / SHRM preferred"],
        "key_responsibilities": [
            "Lead the Talent Management division",
            "Set HR strategy aligned with UAE Vision 2031",
            "Oversee recruitment, L&D, and performance management",
            "Drive Emiratisation targets across federal entities",
            "Report to executive leadership on workforce analytics",
        ],
    },
    "204321": {
        "job_code": "HR-OFF-G6-003", "job_title": "HR Officer",
        "job_family": "HR Operations", "grade": "G6", "step": 1,
        "department": "Recruitment & Selection", "division": "Federal Recruitment",
        "section": "Talent Acquisition", "reporting_to": "HR Director",
        "work_location": "FAHR HQ — Abu Dhabi", "employment_type": "Permanent",
        "contract_type": "Full-Time", "working_hours": "7.5 hours/day — Sunday to Thursday",
        "probation_end_date": "2019-09-30", "confirmation_date": "2019-10-01",
        "years_of_service": 7,
        "qualifications_required": ["Bachelor's in HR, Business Administration, or related field"],
        "key_responsibilities": [
            "Coordinate recruitment campaigns for federal entities",
            "Screen applications and schedule interviews",
            "Manage onboarding process for new joiners",
            "Maintain recruitment records in Bayanati",
            "Prepare monthly recruitment reports",
        ],
    },
}

MOCK_HR_POLICY_CHUNKS = [
    {
        "chunk_id": "hr-001", "document_name": "FAHR Annual Leave Policy 2024",
        "document_id": "doc-hr-001", "page_number": 3, "language": "en",
        "topic": "Human Resources", "subtopic": "annual leave",
        "page_image": "https://fahr.gov.ae/docs/hr-001/page-3.png",
        "text": "Annual Leave Entitlement: Federal government employees are entitled to 30 calendar days of paid annual leave per year upon completing 6 months of service. Employees with less than 6 months are entitled to 2.5 days per month. Leave must be approved by the direct manager at least 7 days in advance. Unused leave up to 15 days may be carried forward to the following year. Any balance exceeding 15 days at year-end is forfeited unless exceptional approval is granted by HR.",
    },
    {
        "chunk_id": "hr-002", "document_name": "FAHR Study Leave Policy 2024",
        "document_id": "doc-hr-002", "page_number": 1, "language": "en",
        "topic": "Human Resources", "subtopic": "study leave",
        "page_image": "https://fahr.gov.ae/docs/hr-002/page-1.png",
        "text": "Study Leave: Employees may apply for paid study leave to pursue higher education directly relevant to their job function. Eligibility requires a minimum of 2 years of continuous service. Study leave is granted for a maximum of 2 years for a Master's degree and 4 years for a PhD. The employee must maintain a minimum grade of B or equivalent. Upon return, the employee must serve at least 2 years for every year of study leave taken.",
    },
    {
        "chunk_id": "hr-003", "document_name": "FAHR Sick Leave Policy 2024",
        "document_id": "doc-hr-003", "page_number": 5, "language": "en",
        "topic": "Human Resources", "subtopic": "sick leave",
        "page_image": "https://fahr.gov.ae/docs/hr-003/page-5.png",
        "text": "Sick Leave: Employees are entitled to 60 days of sick leave per year. The first 15 days are on full pay, the next 30 days on half pay, and the remaining 15 days without pay. A medical certificate from an approved government health facility is mandatory for any sick leave exceeding 3 consecutive days. Sick leave cannot be combined with annual leave without explicit HR approval.",
    },
    {
        "chunk_id": "hr-004", "document_name": "FAHR Remote Work Policy 2024",
        "document_id": "doc-hr-004", "page_number": 2, "language": "en",
        "topic": "Human Resources", "subtopic": "remote work policy",
        "page_image": "https://fahr.gov.ae/docs/hr-004/page-2.png",
        "text": "Remote Work Policy: Federal employees may work remotely up to 2 days per week, subject to manager approval and operational requirements. Employees must remain reachable during official working hours (8:00 AM – 3:30 PM) and maintain the same productivity standards as in-office work. A Remote Work Agreement form must be signed and submitted to HR before the arrangement begins.",
    },
    {
        "chunk_id": "hr-005", "document_name": "FAHR Maternity and Paternity Leave Policy 2024",
        "document_id": "doc-hr-005", "page_number": 4, "language": "en",
        "topic": "Human Resources", "subtopic": "maternity leave",
        "page_image": "https://fahr.gov.ae/docs/hr-005/page-4.png",
        "text": "Maternity Leave: Female employees are entitled to 90 calendar days of paid maternity leave. This may begin up to 30 days before the expected date of birth. An additional 30 days of unpaid maternity leave may be granted upon request. Paternity Leave: Male employees are entitled to 15 calendar days of paid paternity leave to be taken within 6 months of the child's birth.",
    },
    {
        "chunk_id": "hr-006", "document_name": "FAHR Performance Management Framework 2025",
        "document_id": "doc-hr-006", "page_number": 7, "language": "en",
        "topic": "Human Resources", "subtopic": "performance management",
        "page_image": "https://fahr.gov.ae/docs/hr-006/page-7.png",
        "text": "Performance Rating Scale: Outstanding (5.0–4.5), Exceeds Expectations (4.4–3.5), Meets Expectations (3.4–2.5), Needs Improvement (2.4–1.5), Unsatisfactory (below 1.5). Annual increments: Outstanding 8–10%, Exceeds Expectations 5–7%, Meets Expectations 2–4%, Needs Improvement 0%. Employees rated Unsatisfactory for two consecutive years may face disciplinary action including termination.",
    },
    {
        "chunk_id": "hr-007", "document_name": "FAHR Working Hours Policy 2024",
        "document_id": "doc-hr-007", "page_number": 1, "language": "en",
        "topic": "Human Resources", "subtopic": "overtime regulations",
        "page_image": "https://fahr.gov.ae/docs/hr-007/page-1.png",
        "text": "Working Hours: The standard working week for federal employees is 37.5 hours, Sunday through Thursday, 8:00 AM to 3:30 PM. During Ramadan, working hours are reduced to 6 hours per day. Overtime is compensated at 125% of the basic hourly rate for weekday overtime and 150% for Friday and public holiday overtime. Overtime must be pre-approved by the department head.",
    },
    {
        "chunk_id": "hr-008", "document_name": "FAHR Disciplinary Procedures Manual 2024",
        "document_id": "doc-hr-008", "page_number": 9, "language": "en",
        "topic": "Human Resources", "subtopic": "disciplinary actions",
        "page_image": "https://fahr.gov.ae/docs/hr-008/page-9.png",
        "text": "Disciplinary Actions: Minor violations (e.g., repeated lateness) result in a written warning on the first occurrence. A second occurrence within 12 months results in a salary deduction not exceeding 5 days' pay. Serious violations (e.g., fraud, harassment) may result in immediate suspension, salary deduction up to 30 days, demotion, or dismissal. All disciplinary decisions must be communicated in writing with the right to appeal within 15 working days.",
    },
    {
        "chunk_id": "hr-009", "document_name": "FAHR Hajj and Religious Leave Policy 2024",
        "document_id": "doc-hr-009", "page_number": 2, "language": "en",
        "topic": "Human Resources", "subtopic": "employee rights",
        "page_image": "https://fahr.gov.ae/docs/hr-009/page-2.png",
        "text": "Hajj Leave: Muslim employees are entitled to 30 days of paid leave once during their service for the performance of Hajj. This leave is non-cumulative and can only be taken once per employment. Application must be submitted at least 30 days in advance. Emergency Leave: Employees are entitled to 5 days of emergency leave per year for urgent personal matters.",
    },
    {
        "chunk_id": "hr-010", "document_name": "FAHR Promotion and Increment Policy 2025",
        "document_id": "doc-hr-010", "page_number": 3, "language": "en",
        "topic": "Human Resources", "subtopic": "promotions and increments",
        "page_image": "https://fahr.gov.ae/docs/hr-010/page-3.png",
        "text": "Promotions: Employees are eligible for promotion after a minimum of 2 years in their current grade with a performance rating of Exceeds Expectations or above for the last 2 consecutive years. A promotion moves the employee one grade up and includes a minimum 15% increase in basic salary. Grade increments within the same grade occur annually based on performance rating.",
    },
]

MOCK_LEGAL_POLICY_CHUNKS = [
    {
        "chunk_id": "legal-001", "document_name": "UAE Federal Decree-Law No. 49 of 2022 — Human Resources",
        "document_id": "doc-legal-001", "page_number": 12, "language": "en",
        "topic": "Laws and Policies", "subtopic": "federal decrees",
        "page_image": "https://fahr.gov.ae/docs/legal-001/page-12.png",
        "text": "Article 28 — Annual Leave: Federal civil servants shall be entitled to annual leave of not less than 30 calendar days per year with full pay upon completion of one year of service. The competent authority may postpone the employee's leave to the following year provided the employee's consent is obtained. Monetary compensation for untaken leave shall not be permissible except upon termination of service.",
    },
    {
        "chunk_id": "legal-002", "document_name": "UAE Federal Decree-Law No. 49 of 2022 — Human Resources",
        "document_id": "doc-legal-001", "page_number": 18, "language": "en",
        "topic": "Laws and Policies", "subtopic": "labor laws",
        "page_image": "https://fahr.gov.ae/docs/legal-001/page-18.png",
        "text": "Article 35 — Termination of Service: An employee's service may be terminated for reasons including: (a) completion of contract term; (b) resignation accepted by the competent authority; (c) proven incapacity due to health; (d) disciplinary dismissal; or (e) abolition of post. An employee dismissed for disciplinary reasons shall forfeit end-of-service gratuity unless otherwise determined by the disciplinary board.",
    },
    {
        "chunk_id": "legal-003", "document_name": "UAE Federal Law No. 11 of 2008 — Human Resources in Federal Government",
        "document_id": "doc-legal-002", "page_number": 7, "language": "en",
        "topic": "Laws and Policies", "subtopic": "civil service governance",
        "page_image": "https://fahr.gov.ae/docs/legal-002/page-7.png",
        "text": "Article 14 — Grievance Procedures: Any federal employee who considers a decision against them unjust may submit a grievance to the competent authority within 15 working days of being notified. The competent authority must respond within 30 working days. If no response is received, the employee may escalate to FAHR within 15 additional working days. FAHR's decision shall be final and binding.",
    },
    {
        "chunk_id": "legal-004", "document_name": "UAE Federal Decree-Law No. 49 of 2022 — Human Resources",
        "document_id": "doc-legal-001", "page_number": 22, "language": "en",
        "topic": "Laws and Policies", "subtopic": "employment contracts",
        "page_image": "https://fahr.gov.ae/docs/legal-001/page-22.png",
        "text": "Article 41 — End of Service Gratuity: Upon completing 5 or more years of continuous service, an employee shall be entitled to an end-of-service gratuity: one month's basic salary for each of the first 5 years, and one and a half month's basic salary for each year thereafter. The total gratuity shall not exceed 24 months' basic salary.",
    },
    {
        "chunk_id": "legal-005", "document_name": "UAE Federal Law No. 3 of 2022 — Regulating Human Resources AI Use",
        "document_id": "doc-legal-003", "page_number": 4, "language": "en",
        "topic": "Laws and Policies", "subtopic": "authority policies",
        "page_image": "https://fahr.gov.ae/docs/legal-003/page-4.png",
        "text": "Article 9 — Data Privacy in HR Systems: Federal entities must ensure employee personal data is processed lawfully and transparently. Employee data may only be accessed by authorised personnel for legitimate HR purposes. Employees have the right to request access to their personal data and to request correction of inaccurate data. Retention of employee data after service termination is limited to 10 years.",
    },
    {
        "chunk_id": "legal-006", "document_name": "UAE Federal Decree-Law No. 49 of 2022 — Human Resources",
        "document_id": "doc-legal-001", "page_number": 31, "language": "en",
        "topic": "Laws and Policies", "subtopic": "occupational safety and health",
        "page_image": "https://fahr.gov.ae/docs/legal-001/page-31.png",
        "text": "Article 52 — Workplace Safety: Federal entities must provide a safe working environment in accordance with UAE occupational health and safety standards. Employees injured in workplace accidents are entitled to full pay during the recovery period not exceeding 180 days. Employees may not be dismissed during a period of work-related injury or illness.",
    },
    {
        "chunk_id": "legal-007", "document_name": "UAE Federal Law No. 11 of 2008 — Amendments 2021",
        "document_id": "doc-legal-004", "page_number": 3, "language": "en",
        "topic": "Laws and Policies", "subtopic": "federal hiring mechanisms",
        "page_image": "https://fahr.gov.ae/docs/legal-004/page-3.png",
        "text": "Article 6 — Emiratisation Requirements: Federal entities must give priority to UAE nationals in recruitment. Expatriate staff may only be hired when no qualified UAE national is available. All federal recruitment must be conducted through approved FAHR channels. Entities must submit quarterly Emiratisation progress reports to FAHR.",
    },
    {
        "chunk_id": "legal-008", "document_name": "UAE Federal Decree-Law No. 49 of 2022 — Human Resources",
        "document_id": "doc-legal-001", "page_number": 15, "language": "en",
        "topic": "Laws and Policies", "subtopic": "overtime regulations",
        "page_image": "https://fahr.gov.ae/docs/legal-001/page-15.png",
        "text": "Article 32 — Overtime: Federal employees required to work beyond standard hours shall be compensated at not less than 125% of the basic hourly wage for weekday overtime, and 150% for rest days or public holidays. Total overtime hours shall not exceed 2 hours per day or 144 hours per year without exceptional approval.",
    },
    {
        "chunk_id": "legal-009", "document_name": "FAHR Circular No. 2 of 2024 — Remote and Hybrid Work",
        "document_id": "doc-legal-005", "page_number": 1, "language": "en",
        "topic": "Laws and Policies", "subtopic": "remote work policy",
        "page_image": "https://fahr.gov.ae/docs/legal-005/page-1.png",
        "text": "Circular No. 2/2024: Federal entities are authorised to implement hybrid work arrangements not exceeding 40% of total working days per month for eligible employees. Eligibility is determined by the nature of the role, the employee's performance rating (minimum Meets Expectations), and operational requirements.",
    },
    {
        "chunk_id": "legal-010", "document_name": "UAE Personal Data Protection Law — Federal Decree No. 45 of 2021",
        "document_id": "doc-legal-006", "page_number": 8, "language": "en",
        "topic": "Laws and Policies", "subtopic": "HR data privacy",
        "page_image": "https://fahr.gov.ae/docs/legal-006/page-8.png",
        "text": "Article 17 — Employee Rights Under Data Protection Law: Employees have the right to know what personal data is collected about them and who it is shared with. Federal entities acting as data controllers must appoint a Data Protection Officer (DPO) and register with the UAE Data Office. Breach notification to affected employees must occur within 72 hours of a confirmed data breach.",
    },
]

MOCK_CONVERSATION_HISTORY: dict = {}
MOCK_MESSAGE_LOG: list = []


# ─────────────────────────────────────────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────────────────────────────────────────

def _get_employee(person_id: str) -> Optional[dict]:
    return MOCK_EMPLOYEES.get(str(person_id))


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 1 — Duplicate Check
# ─────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def check_duplicate_message(message_id: str) -> dict:
    """
    Check if a message has already been processed.
    Always call this FIRST before doing anything else.
    Returns {is_duplicate: bool}.
    """
    already_seen = any(log.get("message_id") == message_id for log in MOCK_MESSAGE_LOG)
    return {"is_duplicate": already_seen, "message_id": message_id}


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 2 — Get Employee Profile
# ─────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def get_employee_profile(person_id: str) -> dict:
    """
    Fetch complete employee profile including name, role, grade, department, manager.
    Always call this second — needed to personalise every response.
    person_id: employee person ID from session context.
    """
    emp = _get_employee(person_id)
    if not emp:
        return {"found": False, "error": f"No employee found for person_id={person_id}", "available_test_ids": list(MOCK_EMPLOYEES.keys())}
    return {"found": True, "profile": emp}


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 3 — Get Conversation History
# ─────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def get_conversation_history(person_id: str, limit: int = 10) -> dict:
    """
    Fetch the last N conversation turns for this employee.
    Call ONLY when the message appears to reference a previous topic.
    Do NOT call for fresh standalone questions or greetings.
    """
    history = MOCK_CONVERSATION_HISTORY.get(str(person_id), [])
    recent = history[-limit:] if len(history) > limit else history
    return {"person_id": person_id, "message_count": len(recent), "conversation_history": recent}


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 4 — Get Leave Balance
# ─────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def get_leave_balance(person_id: str, leave_type: Optional[str] = None) -> dict:
    """
    Fetch leave balances for an employee.
    person_id: employee person ID.
    leave_type: optional filter e.g. 'Annual Leave', 'Sick Leave'. None returns all types.
    Returns balance, used days, and total entitlement per leave type.
    """
    emp = _get_employee(person_id)
    if not emp:
        return {"found": False, "error": f"Employee {person_id} not found"}
    balances = MOCK_LEAVE_BALANCES.get(str(person_id), [])
    if leave_type:
        balances = [b for b in balances if leave_type.lower() in b["leave_type"].lower() or leave_type.lower() in b.get("leave_type_ar", "").lower()]
    return {"found": True, "person_id": person_id, "employee_name": emp["full_name"], "as_of_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "leave_balances": balances}


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 5 — Get Payslip
# ─────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def get_payslip(person_id: str, period: Optional[str] = None) -> dict:
    """
    Fetch payslip for an employee.
    person_id: employee person ID.
    period: optional period code e.g. '202603' for March 2026, or 'latest'/None for most recent.
    Returns basic salary, allowances, deductions, net salary, bank details.
    """
    emp = _get_employee(person_id)
    if not emp:
        return {"found": False, "error": f"Employee {person_id} not found"}
    slips = MOCK_PAYSLIPS.get(str(person_id), [])
    if not slips:
        return {"found": False, "error": "No payslip records found"}
    if period and period != "latest":
        slips = [s for s in slips if period in s["period_code"] or period.lower() in s["period"].lower()]
        if not slips:
            return {"found": False, "error": f"No payslip found for period {period}"}
    return {"found": True, "person_id": person_id, "employee_name": emp["full_name"], "payslip": slips[0]}


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 6 — Get Attendance
# ─────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def get_attendance(person_id: str, days: int = 10) -> dict:
    """
    Fetch recent attendance records for an employee.
    person_id: employee person ID.
    days: number of recent days to return (default 10).
    Returns check-in/out times, status (Present/Late/Absent/Leave), hours worked.
    """
    emp = _get_employee(person_id)
    if not emp:
        return {"found": False, "error": f"Employee {person_id} not found"}
    records = MOCK_ATTENDANCE.get(str(person_id), [])[:days]
    return {
        "found": True, "person_id": person_id, "employee_name": emp["full_name"],
        "period": f"Last {days} days",
        "summary": {
            "present_days":     sum(1 for r in records if r["status"] == "Present"),
            "late_days":        sum(1 for r in records if r["status"] == "Late"),
            "absent_days":      sum(1 for r in records if r["status"] == "Absent"),
            "leave_days":       sum(1 for r in records if "Leave" in r["status"]),
            "total_late_minutes": sum(r["late_minutes"] for r in records),
        },
        "records": records,
    }


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 7 — Get Performance
# ─────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def get_performance(person_id: str) -> dict:
    """
    Fetch the most recent annual performance appraisal for an employee.
    Returns overall rating, objectives, competencies, manager comments, and increment.
    """
    emp = _get_employee(person_id)
    if not emp:
        return {"found": False, "error": f"Employee {person_id} not found"}
    perf = MOCK_PERFORMANCE.get(str(person_id))
    if not perf:
        return {"found": False, "error": "No appraisal data found"}
    return {"found": True, "person_id": person_id, "employee_name": emp["full_name"], "appraisal": perf}


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 8 — Get CRM Tickets
# ─────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def get_crm_tickets(person_id: str, status_filter: Optional[str] = None) -> dict:
    """
    Fetch support/service tickets for an employee.
    person_id: employee person ID.
    status_filter: optional 'Open' or 'Closed'. None returns all.
    Use when employee asks about ticket status, complaints, or pending requests.
    """
    emp = _get_employee(person_id)
    if not emp:
        return {"found": False, "error": f"Employee {person_id} not found"}
    all_tickets = MOCK_CRM_TICKETS.get(str(person_id), [])
    tickets = [t for t in all_tickets if t["status"].lower() == status_filter.lower()] if status_filter else all_tickets
    return {
        "found": True, "person_id": person_id, "employee_name": emp["full_name"],
        "total_tickets": len(all_tickets),
        "open_tickets":   sum(1 for t in all_tickets if t["status"] == "Open"),
        "closed_tickets": sum(1 for t in all_tickets if t["status"] == "Closed"),
        "tickets": tickets,
    }


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 9 — Get Notifications
# ─────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def get_notifications(person_id: str, unread_only: bool = False) -> dict:
    """
    Fetch notifications for an employee (payslip alerts, leave approvals, policy updates, etc.).
    person_id: employee person ID.
    unread_only: if True returns only unread notifications.
    """
    emp = _get_employee(person_id)
    if not emp:
        return {"found": False, "error": f"Employee {person_id} not found"}
    all_notifs = MOCK_NOTIFICATIONS.get(str(person_id), [])
    notifs = [n for n in all_notifs if not n["read"]] if unread_only else all_notifs
    return {
        "found": True, "person_id": person_id, "employee_name": emp["full_name"],
        "total_notifications": len(all_notifs),
        "unread_count": sum(1 for n in all_notifs if not n["read"]),
        "notifications": notifs,
    }


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 10 — Get Job Card
# ─────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def get_job_card(person_id: str) -> dict:
    """
    Fetch the employee's job card — grade, title, responsibilities, working hours, contract type.
    Use when employee asks about their job description, working hours, or employment terms.
    """
    emp = _get_employee(person_id)
    if not emp:
        return {"found": False, "error": f"Employee {person_id} not found"}
    jc = MOCK_JOB_CARD.get(str(person_id))
    if not jc:
        return {"found": False, "error": "No job card found"}
    return {"found": True, "person_id": person_id, "employee_name": emp["full_name"], "job_card": jc}


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 11 — Get Pending Leave Requests
# ─────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def get_pending_leave_requests(person_id: str) -> dict:
    """
    Fetch leave requests that are pending approval for an employee.
    Use when employee asks about the status of a submitted leave request.
    """
    emp = _get_employee(person_id)
    if not emp:
        return {"found": False, "error": f"Employee {person_id} not found"}
    requests = MOCK_PENDING_LEAVE_REQUESTS.get(str(person_id), [])
    return {"found": True, "person_id": person_id, "employee_name": emp["full_name"], "pending_count": len(requests), "pending_requests": requests}


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 12 — Submit Leave Request
# ─────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def submit_leave_request(person_id: str, leave_type: str, start_date: str, end_date: str, reason: str) -> dict:
    """
    Submit a new leave request on behalf of an employee.
    person_id: employee person ID.
    leave_type: e.g. 'Annual Leave', 'Sick Leave', 'Emergency Leave'.
    start_date: YYYY-MM-DD format.
    end_date: YYYY-MM-DD format.
    reason: brief reason for the leave.
    Returns a request ID and confirmation. Do NOT call without all fields confirmed.
    """
    emp = _get_employee(person_id)
    if not emp:
        return {"success": False, "error": f"Employee {person_id} not found"}
    request_id = f"LR-2026-{random.randint(10000, 99999)}"
    new_request = {
        "request_id": request_id, "leave_type": leave_type,
        "start_date": start_date, "end_date": end_date, "reason": reason,
        "status": "Pending Manager Approval",
        "submitted_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "approver": emp.get("manager_name", "Your Manager"),
    }
    if str(person_id) not in MOCK_PENDING_LEAVE_REQUESTS:
        MOCK_PENDING_LEAVE_REQUESTS[str(person_id)] = []
    MOCK_PENDING_LEAVE_REQUESTS[str(person_id)].append(new_request)
    return {"success": True, "request_id": request_id, "message": f"Leave request submitted. Pending approval from {emp.get('manager_name')}.", "request": new_request}


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 13 — Get Team Members (Manager only)
# ─────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def get_team_members(manager_person_id: str) -> dict:
    """
    Fetch team members and today's attendance/leave status.
    Only valid for managers and directors. Will return access denied for employees.
    manager_person_id: the manager's person ID.
    """
    emp = _get_employee(manager_person_id)
    if not emp:
        return {"found": False, "error": f"Employee {manager_person_id} not found"}
    if emp.get("role") not in ["manager", "admin", "director"]:
        return {"found": False, "error": "Access denied. This tool is only available to managers and above.", "employee_role": emp.get("role")}
    team = MOCK_TEAM_MEMBERS.get(str(manager_person_id), [])
    return {
        "found": True, "manager_id": manager_person_id, "manager_name": emp["full_name"],
        "team_size": len(team),
        "today_summary": {
            "present":  sum(1 for m in team if m["attendance_today"] == "Present"),
            "late":     sum(1 for m in team if m["attendance_today"] == "Late"),
            "on_leave": sum(1 for m in team if m["leave_status"] != "Available"),
            "absent":   sum(1 for m in team if m["attendance_today"] == "Absent"),
        },
        "team_members": team,
    }


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 14 — Search HR Policy (RAG — mock)
# ─────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def search_hr_policy(query: str, language: str = "en") -> dict:
    """
    Search FAHR HR policy documents for information about leave, working hours, benefits,
    performance, promotions, disciplinary procedures, and all internal HR policies.
    Use for ANY question about HR rules, entitlements, or procedures.
    query: user's question or a refined search query.
    language: 'en' or 'ar'.
    Returns relevant policy chunks with document name, page number, and screenshot URL for citation.
    NOTE: Currently returns mock data. Will query ChromaDB when connected.
    """
    # Replace this block with: results = chroma_client.similarity_search(query, filter={"document_type": "hr"}, k=3)
    q = query.lower()
    keywords = q.split()
    scored = []
    for chunk in MOCK_HR_POLICY_CHUNKS:
        score = sum(2 if kw in chunk["subtopic"].lower() else 1 if kw in chunk["text"].lower() else 0 for kw in keywords)
        if score > 0:
            scored.append((score, chunk))
    scored.sort(key=lambda x: x[0], reverse=True)
    top_chunks = [c for _, c in scored[:3]] or MOCK_HR_POLICY_CHUNKS[:2]
    context = "\n\n---\n\n".join(f"[{c['document_name']} | Page {c['page_number']}]\n{c['text']}" for c in top_chunks)
    citations = [{"documentId": c["document_id"], "documentName": c["document_name"], "pageNumber": str(c["page_number"]), "screenshotUrl": c["page_image"], "topic": c["topic"], "subtopic": c["subtopic"]} for c in top_chunks]
    return {"found": len(top_chunks) > 0, "query": query, "language": language, "chunks_returned": len(top_chunks), "context": context, "citations": citations, "source": "mock_chromadb"}


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 15 — Search Legal Policy (RAG — mock)
# ─────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def search_legal_policy(query: str, language: str = "en") -> dict:
    """
    Search UAE labor law and FAHR legal regulation documents.
    Use for ANY question about UAE federal law, employee legal rights, termination, gratuity,
    grievance procedures, data privacy, Emiratisation, or any question referencing a law or decree.
    query: user's question or refined search query.
    language: 'en' or 'ar'.
    Returns relevant legal chunks with law name, article, page number, and screenshot URL.
    NOTE: Currently returns mock data. Will query ChromaDB when connected.
    """
    # Replace this block with: results = chroma_client.similarity_search(query, filter={"document_type": "legal"}, k=3)
    q = query.lower()
    keywords = q.split()
    scored = []
    for chunk in MOCK_LEGAL_POLICY_CHUNKS:
        score = sum(2 if kw in chunk["subtopic"].lower() else 1 if kw in chunk["text"].lower() else 0 for kw in keywords)
        if score > 0:
            scored.append((score, chunk))
    scored.sort(key=lambda x: x[0], reverse=True)
    top_chunks = [c for _, c in scored[:3]] or MOCK_LEGAL_POLICY_CHUNKS[:2]
    context = "\n\n---\n\n".join(f"[{c['document_name']} | Page {c['page_number']}]\n{c['text']}" for c in top_chunks)
    citations = [{"documentId": c["document_id"], "documentName": c["document_name"], "pageNumber": str(c["page_number"]), "screenshotUrl": c["page_image"], "topic": c["topic"], "subtopic": c["subtopic"]} for c in top_chunks]
    return {"found": len(top_chunks) > 0, "query": query, "language": language, "chunks_returned": len(top_chunks), "context": context, "citations": citations, "source": "mock_chromadb"}


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 16 — Log Conversation
# ─────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def log_conversation(
    person_id: str, message_id: str, user_message: str, ai_response: str,
    intent: str, language: str = "en", conversation_state: str = "complete",
    citations: Optional[list] = None,
) -> dict:
    """
    Log the conversation turn to the database.
    ALWAYS call this as the LAST step after generating the reply.
    Never retry if it fails. Never call more than once per turn.
    person_id: employee person ID.
    message_id: unique message identifier.
    user_message: raw message from the user.
    ai_response: final reply text being sent.
    intent: classified intent e.g. 'leave_balance', 'payslip', 'hr_policy', 'greeting'.
    language: 'en' or 'ar'.
    conversation_state: 'complete' or 'pending' (if waiting for user input).
    citations: list of document citations used (for RAG answers).
    """
    log_entry = {
        "person_id": person_id, "message_id": message_id,
        "user_message": user_message, "ai_response": ai_response,
        "intent": intent, "language": language,
        "conversation_state": conversation_state,
        "citations": citations or [],
        "logged_at": datetime.now(timezone.utc).isoformat(),
    }
    MOCK_MESSAGE_LOG.append(log_entry)
    if str(person_id) not in MOCK_CONVERSATION_HISTORY:
        MOCK_CONVERSATION_HISTORY[str(person_id)] = []
    MOCK_CONVERSATION_HISTORY[str(person_id)].append({"role": "user", "content": user_message, "timestamp": log_entry["logged_at"]})
    MOCK_CONVERSATION_HISTORY[str(person_id)].append({"role": "assistant", "content": ai_response, "timestamp": log_entry["logged_at"], "intent": intent})
    return {"success": True, "logged": True, "message_id": message_id, "total_logs": len(MOCK_MESSAGE_LOG)}


# ─────────────────────────────────────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)