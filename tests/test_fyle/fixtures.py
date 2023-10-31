fixtures = {
    'get_my_profile': {
        'data': {
            'org': {
                'currency': 'USD',
                'domain': 'fyleforqvd.com',
                'id': 'orNoatdUnm1w',
                'name': 'Fyle For MS Dynamics Demo',
            },
            'org_id': 'orNoatdUnm1w',
            'roles': [
                'FYLER',
                'VERIFIER',
                'PAYMENT_PROCESSOR',
                'FINANCE',
                'ADMIN',
                'AUDITOR',
            ],
            'user': {
                'email': 'ashwin.t@fyle.in',
                'full_name': 'Joanna',
                'id': 'usqywo0f3nBY'
            },
            'user_id': 'usqywo0f3nBY',
        }
    },
    'accounting_export_response': {
        "count":2,
        "next":"None",
        "previous":"None",
        "results":[
            {
                "id":2,
                "created_at":"2023-10-26T03:24:43.513291Z",
                "updated_at":"2023-10-26T03:24:43.513296Z",
                "type":"FETCHING_REIMBURSABLE_EXPENSES",
                "fund_source":"",
                "mapping_errors":"None",
                "task_id":"None",
                "description":[],
                "status":"IN_PROGRESS",
                "detail":[],
                "sage_300_errors":[],
                "exported_at":"None",
                "workspace":1,
                "expenses":[]
            },
            {
                "id":1,
                "created_at":"2023-10-26T03:24:43.511973Z",
                "updated_at":"2023-10-26T03:24:43.511978Z",
                "type":"FETCHING_CREDIT_CARD_EXPENENSES",
                "fund_source":"",
                "mapping_errors":"None",
                "task_id":"None",
                "description":[],
                "status":"IN_PROGRESS",
                "detail":[],
                "sage_300_errors":[],
                "exported_at":"None",
                "workspace":1,
                "expenses":[]
            }
        ]
    },
    'accounting_export_summary_response': {
        "id":1,
        "created_at":"2023-10-27T04:53:59.287745Z",
        "updated_at":"2023-10-27T04:53:59.287750Z",
        "last_exported_at":"2023-10-27T04:53:59.287618Z",
        "next_export_at":"2023-10-27T04:53:59.287619Z",
        "export_mode":"AUTO",
        "total_accounting_export_count":10,
        "successful_accounting_export_count":5,
        "failed_accounting_export_count":5,
        "workspace":1
    },
    "errors_response": {
        "count":3,
        "next":"None",
        "previous":"None",
        "results":[
            {
                "id":1,
                "created_at":"2023-10-26T03:47:16.864421Z",
                "updated_at":"2023-10-26T03:47:16.864428Z",
                "type":"EMPLOYEE_MAPPING",
                "is_resolved": "false",
                "error_title":"Employee Mapping Error",
                "error_detail":"Employee Mapping Error",
                "workspace":1,
                "accounting_export":"None",
                "expense_attribute":"None"
            },
            {
                "id":2,
                "created_at":"2023-10-26T03:47:16.865103Z",
                "updated_at":"2023-10-26T03:47:16.865108Z",
                "type":"CATEGORY_MAPPING",
                "is_resolved": "false",
                "error_title":"Category Mapping Error",
                "error_detail":"Category Mapping Error",
                "workspace":1,
                "accounting_export":"None",
                "expense_attribute":"None"
            },
            {
                "id":3,
                "created_at":"2023-10-26T03:47:16.865303Z",
                "updated_at":"2023-10-26T03:47:16.865307Z",
                "type":"SAGE300_ERROR",
                "is_resolved": "false",
                "error_title":"Sage Error",
                "error_detail":"Sage Error",
                "workspace":1,
                "accounting_export":"None",
                "expense_attribute":"None"
            }
        ]
    },
}
