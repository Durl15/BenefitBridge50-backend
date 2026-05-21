OFFICIAL_RESOURCES = [
    {
        "id": "snap-usda",
        "program_code": "SNAP",
        "program_name": "Supplemental Nutrition Assistance Program",
        "category": "Food",
        "state": "US",
        "official_url": "https://www.fns.usda.gov/snap/state-directory",
        "description": "Official USDA state directory for food assistance applications."
    },
    {
        "id": "ssi-ssa",
        "program_code": "SSI",
        "program_name": "Supplemental Security Income",
        "category": "Income",
        "state": "US",
        "official_url": "https://www.ssa.gov/ssi/",
        "description": "Official Social Security Administration information on SSI."
    },
    {
        "id": "msp-medicare",
        "program_code": "MSP",
        "program_name": "Medicare Savings Programs",
        "category": "Health coverage costs",
        "state": "US",
        "official_url": "https://www.medicare.gov/basics/costs/help/medicare-savings-programs",
        "description": "Official Medicare information on help paying Medicare premiums and cost sharing."
    },
    {
        "id": "liheap-hhs",
        "program_code": "LIHEAP",
        "program_name": "Low Income Home Energy Assistance Program",
        "category": "Utilities",
        "state": "US",
        "official_url": "https://www.acf.hhs.gov/ocs/low-income-home-energy-assistance-program-liheap",
        "description": "Official HHS information on help with home energy costs."
    },
    {
        "id": "hud-housing",
        "program_code": "HUD-HOUSING",
        "program_name": "HUD Rental Assistance and Housing Counseling",
        "category": "Housing",
        "state": "US",
        "official_url": "https://www.hud.gov/topics/rental_assistance",
        "description": "Official HUD rental assistance resources."
    },
    {
        "id": "eldercare-locator",
        "program_code": "ELDERCARE",
        "program_name": "Eldercare Locator",
        "category": "Local support",
        "state": "US",
        "official_url": "https://eldercare.acl.gov/Public/Index.aspx",
        "description": "Official ACL locator for Area Agencies on Aging and local services."
    },
    {
        "id": "benefitscheckup",
        "program_code": "BCU",
        "program_name": "BenefitsCheckUp",
        "category": "Benefits discovery",
        "state": "US",
        "official_url": "https://benefitscheckup.org/",
        "description": "NCOA benefits screening resource for older adults and people with disabilities."
    },
    {
        "id": "aarp-fraud-watch",
        "program_code": "FRAUD-WATCH",
        "program_name": "AARP Fraud Watch Network",
        "category": "Fraud prevention",
        "state": "US",
        "official_url": "https://www.aarp.org/money/scams-fraud/",
        "description": "AARP scam prevention education and fraud reporting guidance."
    }
]

RESOURCE_BY_CODE = {item["program_code"]: item for item in OFFICIAL_RESOURCES}
