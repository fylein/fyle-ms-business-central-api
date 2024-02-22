data = {
    "accounting_export": {
        "type": "JOURNAL_ENTRY",
        "fund_source": "PERSONAL",
        "mapping_errors": ["Error 1", "Error 2"],
        "expenses": ["Expense1", "Expense2"],
        "task_id": "task123",
        "export_url": "https://example.com/export",
        "description": {
            "expense_id": "ABCDEF123",
            "fund_source": "PERSONAL",
            "employee_email": "ashwin.t@fyle.in",
            "expense_number": "E/2023/04/T/31"
        },
        "status": "Exported",
        "detail": {"key": "value"},
        "business_central_errors": {"error": "Something went wrong"},
        "exported_at": "2024-02-15T12:00:00Z"
    },
    "export_settings": {
        "workspace_id": 1,
        "reimbursable_expenses_export_type": "JOURNAL_ENTRY",
        "default_bank_account_name": "Bank of Example",
        "default_bank_account_id": "123456789",
        "reimbursable_expense_state": "PAYMENT_PROCESSING",
        "reimbursable_expense_date": "LAST_SPENT_AT",
        "reimbursable_expense_grouped_by": "REPORT",
        "credit_card_expense_export_type": "JOURNAL_ENTRY",
        "credit_card_expense_state": "APPROVED",
        "credit_card_expense_grouped_by": "REPORT",
        "credit_card_expense_date": "LAST_SPENT_AT",
        "default_vendor_name": "Vendor X",
        "default_vendor_id": "987654321",
        "journal_entry_folder_id": "folder123",
        "employee_field_mapping": "EMPLOYEE",
        "name_in_journal_entry": "EMPLOYEE",
        "auto_map_employees": "NAME"
    },
    "advanced_setting": {
        "workspace_id": 1,
        "expense_memo_structure": ["Field1", "Field2", "category", "employee_email"],
        "schedule_is_enabled": True,
        "start_datetime": "2024-02-15T08:00:00Z",
        "schedule_id": "schedule123",
        "interval_hours": 24,
        "emails_selected": ["email1@example.com", "email2@example.com"],
        "emails_added": ["newemail@example.com"],
        "auto_create_vendor": False
    },
    "employee_expense_attributes": {
        "attribute_type": "EMPLOYEE",
        "value": "ashwin.t@fyle.in",
        "display_name": "Employee One",
        "active": True,
        "source_id": "source123",
    },
    "employee_destination_attributes": {
        "attribute_type": "EMPLOYEE",
        "value": "hello.world@test.in",
        "display_name": "Employee One",
        "active": True,
        "destination_id": "destination123",
    },
    "vendor_destination_attributes": {
        "attribute_type": "Vendor",
        "value": "Ashwin",
        "display_name": "Ashwin",
        "active": True,
        "destination_id": "dest_vendor123",
    },
    "category_expense_attributes": {
        "attribute_type": "CATEGORY",
        "value": "Food",
        "display_name": "Food",
        "active": True,
        "source_id": "src_category123",
    },
    "category_destination_attributes": {
        "attribute_type": "CATEGORY",
        "value": "Food",
        "display_name": "Food",
        "active": True,
        "destination_id": "dest_category123",
    },
    "expenses":[
        {
            'id':91,
            'employee_email':'ashwin.t@fyle.in',
            'employee_name':'Joanna',
            'category':'Food',
            'sub_category':None,
            'project':'Aaron Abbott',
            'org_id':'or79Cob97KSh',
            'expense_id':'txxTi9ZfdepC',
            'expense_number':'E/2022/05/T/16',
            'claim_number':'C/2022/05/R/4',
            'report_title':'R/2022/05/R/4',
            'amount':50.0,
            'currency':'USD',
            'foreign_amount':None,
            'foreign_currency':None,
            'tax_amount':None,
            'tax_group_id':None,
            'settlement_id':'setDiksMn83K7',
            'reimbursable':True,
            'billable':False,
            'exported':False,
            'state':'PAYMENT_PROCESSING',
            'vendor':'Ashwin',
            'cost_center':'Marketing',
            'purpose':None,
            'report_id':'rpViBmuYmAgw',
            'corporate_card_id':None,
            'file_ids':[

            ],
            'spent_at':'2022-05-13T17:00:00Z',
            'approved_at':'2022-05-13T09:30:13.484000Z',
            'posted_at': '2021-12-22T07:30:26.289842+00:00',
            'expense_created_at':'2022-05-13T09:29:43.535468Z',
            'expense_updated_at':'2022-05-13T09:32:06.643941Z',
            'created_at':'2022-05-23T11:11:28.241406Z',
            'updated_at':'2022-05-23T11:11:28.241440Z',
            'fund_source':'PERSONAL',
            'source_account_type': 'PERSONAL_CASH_ACCOUNT',
            'verified_at':'2022-05-23T11:11:28.241440Z',
            'custom_properties':{
                'Team':'',
                'Class':'',
                'Klass':'',
                'Location':'',
                'Team Copy':'',
                'Tax Groups':'',
                'Departments':'',
                'Team 2 Postman':'',
                'User Dimension':'',
                'Location Entity':'',
                'Operating System':'',
                'System Operating':'',
                'User Dimension Copy':'',
                'Custom Expense Field':'None'
            },
            'paid_on_qbo':False,
            'payment_number':'P/2022/05/R/7'
        }
    ],
    "expense_fields": [
        {
            'field_name': 'EMPLOYEE',
            'id': 1,
            'is_enabled': True
        },
        {
            'field_name': 'CATEGORY',
            'id': 2,
            'is_enabled': True
        },
        {
            'field_name': 'VENDOR',
            'id': 3,
            'is_enabled': True
        },
        {
            'field_name': 'PROJECT',
            'id': 4,
            'is_enabled': True
        },
        {
            'field_name': 'COST_CENTER',
            'id': 5,
            'is_enabled': True
        },
        {
            'field_name': 'LOCATION',
            'id': 6,
            'is_enabled': True
        }
    ],
    "included_fields": [
        'EMPLOYEE',
        'CATEGORY',
        'VENDOR',
        'PROJECT',
        'COST_CENTER',
        'LOCATION'
    ]
}
