import pandas as pd
import numpy as np
from faker import Faker
import random

fake = Faker("en_US")
np.random.seed(42)

N_CUSTOMERS = 12000
N_TXN = 20000

# -------------------------
# Customers
# -------------------------
customers = []
for i in range(N_CUSTOMERS):
    customers.append({
        "customer_id": i + 1,
        "customer_code": f"CUST{i+1:06d}",
        "full_name": fake.name(),
        "dob": fake.date_of_birth(minimum_age=18, maximum_age=75),
        "gender": random.choice(["M", "F"]),
        "national_id": fake.ssn(),
        "segment": random.choice(["Retail", "SME", "Corporate"]),
        "target_code": random.choice(["T1", "T2", "T3"]),
        "sector_code": random.choice(["S1", "S2", "S3"]),
        "industry_code": random.choice(["I1", "I2", "I3"]),
    })

df_cus = pd.DataFrame(customers)
df_cus.to_csv("customers.csv", index=False)


# -------------------------
# Transactions
# -------------------------
products = ["LN_HOME", "LN_AUTO", "LN_BUSINESS",
            "DP_SAVING", "DP_CURRENT", "DP_TERM"]

transactions = []
for i in range(N_TXN):
    cid = np.random.randint(1, N_CUSTOMERS)
    prod = random.choice(products)

    transactions.append({
        "txn_id": f"TX{i+1:08d}",
        "customer_id": cid,
        "product_code": prod,
        "branch_code": f"BR{np.random.randint(1,50):03d}",
        "amount": round(np.random.uniform(1_000_000, 2_000_000_000), 2),
        "currency": random.choice(["VND", "USD", "EUR"]),
        "value_date": fake.date_between(start_date='-365d', end_date='today'),
        "maturity_date": fake.date_between(start_date='today', end_date='+180d'),
        "interest_rate": round(np.random.uniform(3.0, 13.0), 2),
        "txn_type": "LOAN" if "LN" in prod else "DEPOSIT",
        "create_date": fake.date_between(start_date='-365d', end_date='today')
    })

df_txn = pd.DataFrame(transactions)
df_txn.to_csv("transactions.csv", index=False)

print("Generated 12k customers + 20k transactions!")