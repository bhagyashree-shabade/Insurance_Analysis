def preprocess_insurance_data(csv_file_path):
    """
    Preprocess insurance claims CSV data, handling missing/invalid values and data types.
    Args:
        csv_file_path (str): Path to the CSV file or string buffer.
    Returns:
        list: List of dictionaries with cleaned data.
    """
    cleaned_data = []
    
    if isinstance(csv_file_path, str) and '\n' in csv_file_path:
        lines = csv_file_path.strip().split('\n')
    else:
        with open(csv_file_path, 'r') as file:
            lines = file.readlines()
    
    headers = lines[0].strip().split(',')
    
    for line in lines[1:]:
        row = line.strip().split(',')
        if len(row) != len(headers):
            continue  
        
        cleaned_row = {}
        
        # Process each column
        for i, (header, value) in enumerate(zip(headers, row)):
            if header == 'CLAIM_ID':
                cleaned_row[header] = value if value.strip() else None
            elif header == 'CLAIM_DATE':
                cleaned_row[header] = value if value.strip() and is_valid_date(value) else None
            elif header == 'CUSTOMER_ID':
                cleaned_row[header] = value if value.strip() else None
            elif header in ['CLAIM_AMOUNT', 'PREMIUM_COLLECTED', 'PAID_AMOUNT']:
                try:
                    cleaned_row[header] = float(value) if value.strip() else 0.0
                except ValueError:
                    cleaned_row[header] = 0.0
            elif header == 'CITY':
                cleaned_row[header] = value.strip().upper() if value.strip() else None
            elif header == 'REJECTION_REMARKS':
                cleaned_row[header] = value.strip() if value.strip() else ''
        
        # Skip rows with critical missing data
        if cleaned_row['CLAIM_ID'] and cleaned_row['CUSTOMER_ID']:
            cleaned_data.append(cleaned_row)
    
    return cleaned_data

def is_valid_date(date_str):
    """
    Validate date string in YYYY-MM-DD format.
    """
    try:
        year, month, day = map(int, date_str.split('-'))
        if 1 <= month <= 12 and 1 <= day <= 31 and year >= 2025:
            return True
        return False
    except (ValueError, TypeError):
        return False

def analyze_city_performance(csv_file_path):
    """
    Analyze insurance claims data to recommend a city for closure.
    """
    data = preprocess_insurance_data(csv_file_path)
    
    city_metrics = {
        city: {
            'claim_count': 0,
            'total_claim_amount': 0.0,
            'total_paid_amount': 0.0,
            'total_premium': 0.0,
            'rejected_count': 0,
            'loss_ratio': 0.0
        }
        for city in ['PUNE', 'KOLKATA', 'RANCHI', 'GUWAHATI']
    }
    
    for row in data:
        city = row['CITY']
        if city not in city_metrics:
            continue
        city_metrics[city]['claim_count'] += 1
        city_metrics[city]['total_claim_amount'] += row['CLAIM_AMOUNT']
        city_metrics[city]['total_paid_amount'] += row['PAID_AMOUNT']
        city_metrics[city]['total_premium'] += row['PREMIUM_COLLECTED']
        if row['REJECTION_REMARKS']:
            city_metrics[city]['rejected_count'] += 1
    
    for city in city_metrics:
        claims = city_metrics[city]['total_claim_amount']
        premiums = city_metrics[city]['total_premium']
        city_metrics[city]['loss_ratio'] = (city_metrics[city]['total_paid_amount'] / premiums) if premiums > 0 else 0.0
        city_metrics[city]['rejection_rate'] = (city_metrics[city]['rejected_count'] / city_metrics[city]['claim_count']) if city_metrics[city]['claim_count'] > 0 else 0.0
    
    scores = {}
    for city in city_metrics:
        loss_ratio = city_metrics[city]['loss_ratio']
        rejection_rate = city_metrics[city]['rejection_rate']
        claim_count = city_metrics[city]['claim_count']
        score = (loss_ratio * 0.5) + (rejection_rate * 0.3) - (claim_count / 100 * 0.2)
        scores[city] = score
    
    recommended_city = max(scores, key=scores.get) if scores else None
    
    return {
        'metrics': city_metrics,
        'recommendation': recommended_city,
        'reason': f'{recommended_city} has high loss ratio and rejection rate, indicating operational inefficiencies.'
    }

def complex_rejection_classifier(remark):
    """
    Classify rejection remarks into categories.
    """
    if not isinstance(remark, str):
        return 'Other'
    
    remark = remark.lower()
    if 'expired' in remark or 'policy_expired' in remark:
        return 'Policy Expired'
    elif 'fake' in remark or 'fake_document' in remark:
        return 'Fake Document'
    elif 'covered' in remark or 'not_covered' in remark:
        return 'Not Covered'
    return 'Other'

def add_rejection_class(data):
    """
    Add REJECTION_CLASS to preprocessed data.
    """
    for row in data:
        remark = row['REJECTION_REMARKS']
        row['REJECTION_CLASS'] = complex_rejection_classifier(remark) if remark else 'No Remark'
    return data

def main():
    csv_data = """CLAIM_ID,CLAIM_DATE,CUSTOMER_ID,CLAIM_AMOUNT,PREMIUM_COLLECTED,PAID_AMOUNT,CITY,REJECTION_REMARKS
CLM100021,2025-04-01,CUST14285,10419.0,2198.59,6964.46,PUNE,
CLM100013,2025-04-01,CUST26471,42468.0,8982.2,30119.67,GUWAHATI,
CLM100099,2025-04-02,CUST29309,55897.0,1861.78,55657.15,GUWAHATI,
CLM100044,2025-04-02,CUST30275,71785.0,13154.99,53629.3,PUNE,
CLM100014,2025-04-02,CUST38169,18565.0,2606.4,12849.24,RANCHI,
CLM100062,2025-04-02,CUST41634,84513.0,11166.17,84503.26,KOLKATA,
CLM100010,2025-04-03,CUST52415,22774.0,15202.22,12105.48,KOLKATA,
CLM100012,2025-04-03,CUST19944,22162.0,5361.39,19091.03,RANCHI,
CLM100029,2025-04-04,CUST62992,3196.0,11752.93,2084.27,PUNE,
CLM100053,2025-04-04,CUST11673,27306.0,8940.45,24832.11,PUNE,
CLM100054,2025-04-04,CUST37231,26367.0,1909.22,22294.92,PUNE,
CLM100006,2025-04-05,CUST40797,83571.0,3461.14,68199.38,PUNE,
CLM100001,2025-04-05,CUST71468,12164.0,16583.82,6495.73,GUWAHATI,
CLM100003,2025-04-05,CUST71877,99944.0,3081.83,79950.47,PUNE,
CLM100061,2025-04-05,CUST74127,72838.0,5126.2,65347.46,RANCHI,
CLM100085,2025-04-06,CUST31609,89362.0,,71995.54,KOLKATA,
CLM100080,2025-04-06,CUST38358,73417.0,8409.15,59605.08,GUWAHATI,
CLM100089,2025-04-06,CUST80026,56281.0,,47278.36,KOLKATA,
CLM100027,2025-04-06,CUST14047,,13263.85,53417.11,PUNE,
CLM100063,2025-04-06,CUST79802,53521.0,6786.32,34028.19,GUWAHATI,
CLM100070,2025-04-07,CUST86689,51976.0,16601.46,26393.35,PUNE,
CLM100081,2025-04-07,CUST52716,12185.0,6212.4,11878.02,RANCHI,
CLM100068,2025-04-07,CUST86414,31302.0,3032.33,16219.79,PUNE,
CLM100094,2025-04-07,CUST54178,31102.0,,20968.0,KOLKATA,
CLM100066,2025-04-07,CUST94430,62146.0,17861.9,59642.65,GUWAHATI,
CLM100033,2025-04-08,CUST36174,57183.0,19074.86,51997.18,GUWAHATI,
CLM100039,2025-04-08,CUST83721,,12015.1,25254.26,PUNE,
CLM100009,2025-04-08,CUST58755,7617.0,18799.38,6209.87,KOLKATA,
CLM100051,2025-04-09,CUST17594,52569.0,17115.96,,PUNE,
CLM100024,2025-04-09,CUST47907,37076.0,11890.44,19712.25,GUWAHATI,
CLM100074,2025-04-09,CUST62428,9462.0,13550.16,5488.19,,
CLM100038,2025-04-10,CUST55227,15564.0,19124.37,0.0,PUNE,Rejection reason: Policy_expired in verification.
CLM100071,2025-04-10,CUST47050,10713.0,18997.84,7686.44,,
CLM100059,2025-04-10,CUST37384,72187.0,6783.05,0.0,RANCHI,Policy rejected: Policy_expired noted.
CLM100064,2025-04-10,CUST40607,92874.0,1266.93,73616.75,PUNE,
CLM100077,2025-04-11,CUST70532,46302.0,17194.67,,KOLKATA,
CLM100041,2025-04-11,CUST79328,20085.0,19732.25,17160.03,PUNE,
CLM100015,2025-04-11,CUST25245,82101.0,15528.72,44593.86,GUWAHATI,
CLM100046,2025-04-11,CUST67393,93851.0,17094.9,75977.26,PUNE,
CLM100048,2025-04-11,CUST74020,80637.0,18734.5,51017.11,GUWAHATI,
CLM100035,2025-04-12,CUST20759,95554.0,8777.64,73607.73,KOLKATA,
CLM100005,2025-04-12,CUST83128,41913.0,2716.16,33556.69,KOLKATA,
CLM100072,2025-04-12,CUST23811,62307.0,4772.41,35170.41,GUWAHATI,
CLM100098,2025-04-12,CUST49836,54580.0,3119.67,33131.76,GUWAHATI,
CLM100088,2025-04-12,CUST94145,11703.0,16757.23,10400.91,,
CLM100083,2025-04-13,CUST46233,5966.0,8287.39,3293.54,PUNE,
CLM100011,2025-04-13,CUST92038,45399.0,14217.07,,PUNE,
CLM100079,2025-04-13,CUST54690,11641.0,3647.67,6107.55,RANCHI,
CLM100032,2025-04-13,CUST87247,51984.0,11243.23,32544.37,RANCHI,
CLM100047,2025-04-13,CUST74101,54838.0,13819.25,44196.44,KOLKATA,
CLM100042,2025-04-13,CUST78196,94552.0,1210.25,70590.7,PUNE,
CLM100036,2025-04-14,CUST47615,,6587.82,56276.31,GUWAHATI,
CLM100096,2025-04-14,CUST24471,15373.0,10412.56,0.0,PUNE,Fake_document reason led to rejection.
CLM100023,2025-04-14,CUST70928,48394.0,8943.6,34060.76,PUNE,
CLM100040,2025-04-14,CUST91411,71767.0,4498.04,49712.78,KOLKATA,
CLM100057,2025-04-14,CUST45154,53345.0,9841.35,35581.93,PUNE,
CLM100018,2025-04-14,CUST67706,39474.0,15963.13,29157.41,GUWAHATI,
CLM100025,2025-04-15,CUST22223,40273.0,13409.84,40178.95,PUNE,
CLM100037,2025-04-15,CUST48926,67380.0,14990.53,51840.71,PUNE,
CLM100084,2025-04-15,CUST72294,56827.0,9789.26,44849.17,RANCHI,
CLM100022,2025-04-17,CUST31412,,5546.68,66651.78,RANCHI,
CLM100028,2025-04-17,CUST86005,23208.0,16323.3,16631.13,RANCHI,
CLM100090,2025-04-17,CUST61146,85451.0,14714.23,0.0,GUWAHATI,Claim denied due to Policy_expired.
CLM100019,2025-04-17,CUST95453,21642.0,18385.11,20046.96,RANCHI,
CLM100073,2025-04-17,CUST34675,67602.0,2656.62,37244.58,KOLKATA,
CLM100034,2025-04-18,CUST60297,58385.0,12168.04,43064.57,KOLKATA,
CLM100008,2025-04-18,CUST72188,37753.0,15042.85,29044.48,GUWAHATI,
CLM100067,2025-04-18,CUST31021,38451.0,11354.22,33580.6,PUNE,
CLM100004,2025-04-19,CUST71295,43151.0,3932.34,32412.52,GUWAHATI,
CLM100076,2025-04-20,CUST27073,55203.0,17307.3,29700.27,PUNE,
CLM100052,2025-04-20,CUST35707,46039.0,12354.28,34708.77,KOLKATA,
CLM100092,2025-04-21,CUST65606,28825.0,15191.11,14906.21,GUWAHATI,
CLM100069,2025-04-21,CUST89363,4794.0,11519.13,3420.0,PUNE,
CLM100082,2025-04-21,CUST26812,45035.0,2337.22,37473.96,GUWAHATI,
CLM100058,2025-04-21,CUST65550,,17190.78,39381.02,PUNE,
CLM100087,2025-04-21,CUST75350,34255.0,12149.78,24161.34,RANCHI,
CLM100031,2025-04-22,CUST72777,6543.0,,6149.32,PUNE,
CLM100086,2025-04-22,CUST93808,97179.0,5383.46,0.0,,Case flagged as Policy_expired during audit.
CLM100020,2025-04-22,CUST15146,25955.0,14383.19,19582.9,GUWAHATI,
CLM100045,2025-04-22,CUST73630,76086.0,,0.0,GUWAHATI,System flagged this claim: Policy_expired.
CLM100000,2025-04-23,CUST79897,23164.0,10851.42,0.0,,Policy rejected: Fake_document noted.
CLM100049,2025-04-23,CUST46039,66543.0,19142.38,34892.81,GUWAHATI,
CLM100093,2025-04-24,CUST30745,38181.0,12022.08,,RANCHI,
CLM100075,2025-04-24,CUST34377,43227.0,8453.1,32720.2,,
CLM100065,2025-04-24,CUST82241,31317.0,6307.06,30244.87,PUNE,
CLM100017,2025-04-24,CUST59251,58151.0,10626.35,0.0,RANCHI,Rejection reason: Policy_expired in verification.
CLM100078,2025-04-25,CUST80454,24699.0,5851.0,17885.24,RANCHI,
CLM100060,2025-04-25,CUST55798,59929.0,13563.37,32968.92,PUNE,
CLM100050,2025-04-26,CUST61909,64932.0,7251.53,43521.55,PUNE,
CLM100016,2025-04-26,CUST36362,,14955.09,63099.38,RANCHI,
CLM100097,2025-04-26,CUST87865,39241.0,,21373.44,PUNE,
CLM100026,2025-04-27,CUST93929,,15058.27,22922.66,KOLKATA,
CLM100091,2025-04-27,CUST83317,51803.0,2229.61,,RANCHI,
CLM100095,2025-04-27,CUST65460,31381.0,11489.06,24469.29,PUNE,
CLM100055,2025-04-28,CUST90265,85995.0,12605.77,0.0,PUNE,Rejection reason: Not_Covered in verification.
CLM100056,2025-04-29,CUST80279,21842.0,10931.83,18271.79,GUWAHATI,
CLM100043,2025-04-29,CUST13980,4418.0,9482.97,0.0,GUWAHATI,Submission error - Not_Covered found.
CLM100030,2025-04-29,CUST59921,73844.0,5869.04,54317.84,KOLKATA,
CLM100007,2025-04-29,CUST83981,16816.0,6081.99,12221.81,PUNE,
CLM100002,2025-04-29,CUST87852,57826.0,9525.69,34702.14,PUNE,
"""
    
    cleaned_data = preprocess_insurance_data(csv_data)
    
    cleaned_data_with_class = add_rejection_class(cleaned_data)
    
    analysis_result = analyze_city_performance(csv_data)
    
    print("Sample Cleaned Data with Rejection Class:")
    for row in cleaned_data_with_class:
        print(row)
    
    print("\nCity Analysis Result:")
    print(f"Recommendation: Close operations in {analysis_result['recommendation']}")
    print(f"Reason: {analysis_result['reason']}")
    print("Metrics:")
    for city, metrics in analysis_result['metrics'].items():
        print(f"{city}:")
        print(f"  Claim Count: {metrics['claim_count']}")
        print(f"  Total Claim Amount: ${metrics['total_claim_amount']:.2f}")
        print(f"  Total Paid Amount: ${metrics['total_paid_amount']:.2f}")
        print(f"  Total Premium: ${metrics['total_premium']:.2f}")
        print(f"  Rejected Count: {metrics['rejected_count']}")
        print(f"  Loss Ratio: {metrics['loss_ratio']:.2f}")
        print(f"  Rejection Rate: {metrics['rejection_rate']:.2%}")

if __name__ == "__main__":
    main()