import pandas as pd

data = {
    "Category": ["Salary", "Freelance", "Rent", "Food", "Transport", "Subscriptions"],
    "Type": ["Income", "Income", "Expense", "Expense", "Expense", "Expense"],
    "Amount": [1900, 350, 750, 280, 120, 45]
}

df = pd.DataFrame(data)

income = df[df["Type"] == "Income"]["Amount"].sum()
expenses = df[df["Type"] == "Expense"]["Amount"].sum()
cash_flow = income - expenses

print("Finance & Cash Flow Summary")
print("---------------------------")
print(f"Total income: £{income}")
print(f"Total expenses: £{expenses}")
print(f"Net cash flow: £{cash_flow}")
