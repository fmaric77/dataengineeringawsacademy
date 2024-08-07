#%%
import csv
from dataclasses import dataclass
import datetime as dt
import pandas as pd


# 1 - 3
class CSVHandler:
    def __init__(self, filename):
        self.filename = filename

    def write_to_file(self, header, content):
        with open(self.filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(header)
            writer.writerows(content)

    def read_from_file(self):
        with open(self.filename, mode='r', newline='') as file:
            reader = csv.reader(file)
            rows = list(reader)
            for row in rows[:3]:
                print(row)

header = ["Date", "Invoice Number", "Customer", "Invoiced Amount", "Invoiced Quantity"]
content = [
    [dt.date(2020, 1, 1), 73984, "John Wayne", 500.0, 2.0],
    [dt.date(2020, 1, 12), 51341, "Michael Johnson", 125.0, 3.5],
    [dt.date(2020, 1, 31), 43210, "Stuart Smith", 1200.0, 1.0],
]

csv_handler = CSVHandler('task_1.csv')
csv_handler.write_to_file(header, content)
csv_handler.read_from_file()
#%%
#4- 5 & EXTRA
class InvoiceProcessor:
    @staticmethod
    def find_min_invoiced_amount(filename):
        df = pd.read_csv(filename)
        min_row = df.loc[df['Invoiced Amount'].idxmin()]
        return min_row
    
    @staticmethod
    def calculate_total_invoiced_amount(filename, customer):
        df = pd.read_csv(filename)
        customer_df = df[df['Customer'] == customer].copy()
        customer_df.loc[:, 'Total Value'] = customer_df['Invoiced Amount'] * customer_df['Invoiced Quantity']
        total_sum = customer_df['Total Value'].sum()
        return total_sum

    @staticmethod
    def calculate_total_invoice_value(filename):
        df = pd.read_csv(filename)
        df['Total Value'] = df['Invoiced Amount'] * df['Invoiced Quantity']
        total_value = df['Total Value'].sum()
        return total_value
    
    @staticmethod
    def add_invoice_total_column(filename, output_filename):
        df = pd.read_csv(filename)
        df['Invoice Total'] = df['Invoiced Amount'] * df['Invoiced Quantity']
        df.to_csv(output_filename, index=False)
        print(f"Task 2 EXTRA: Data with 'Invoice Total' column written to {output_filename}")

min_invoiced_amount_row = InvoiceProcessor.find_min_invoiced_amount('task_1.csv')
print(f"Task 4: {min_invoiced_amount_row}")

total_invoiced_amount = InvoiceProcessor.calculate_total_invoiced_amount('task_1.csv', 'Michael Johnson')
print(f"Task 5: Total Invoiced Amount for Michael Johnson: {total_invoiced_amount}")

#%%
total_invoice_value = InvoiceProcessor.calculate_total_invoice_value('task_1.csv')
print(f"Task 1 EXTRA: Total Invoice Value: {total_invoice_value}")
#%%

InvoiceProcessor.add_invoice_total_column('task_1.csv', 'extra_3.csv')
# %%
# TASK 3 EXTRA
@dataclass
class CSVMerger:
    file1: str
    file2: str
    output_file: str
    common_column: str

    def merge_csv_files(self):
        df1 = pd.read_csv(self.file1)
        df2 = pd.read_csv(self.file2)
        
        merged_df = pd.merge(df1, df2, on=self.common_column)
        
        merged_df.to_csv(self.output_file, index=False)
        print(f"TASK 3 EXTRA: Merged data written to {self.output_file}")

merger = CSVMerger(file1='task_1.csv', file2='extra_3.csv', output_file='merged.csv', common_column='Invoice Number')
merger.merge_csv_files()
# %%
## TASKS EXTRA EXTRA
from dataclasses import dataclass
import datetime as dt

@dataclass
class Invoice:
    date: dt.date
    invoice_number: int
    customer: str
    invoiced_amount: float
    invoiced_quantity: float

    def __add__(self, other):
        if not isinstance(other, Invoice):
            return NotImplemented
        new_date = min(self.date, other.date) 
        new_invoice_number = min(self.invoice_number, other.invoice_number)  
        new_customer = f"{self.customer} & {other.customer}"  
        new_invoiced_amount = self.invoiced_amount + other.invoiced_amount  
        new_invoiced_quantity = self.invoiced_quantity + other.invoiced_quantity  
        return self.__class__(new_date, new_invoice_number, new_customer, new_invoiced_amount, new_invoiced_quantity)

    def __sub__(self, other):
        if not isinstance(other, Invoice):
            return NotImplemented
        new_date = self.date  
        new_invoice_number = self.invoice_number 
        new_customer = f"{self.customer} - {other.customer}" 

        new_invoiced_amount = self.invoiced_amount - other.invoiced_amount
        if new_invoiced_amount < 0:
            new_invoiced_amount = f"Credit {abs(new_invoiced_amount)}"

        new_invoiced_quantity = self.invoiced_quantity - other.invoiced_quantity
        if new_invoiced_quantity < 0:
            new_invoiced_quantity = f"Credit {abs(new_invoiced_quantity)}"

        return self.__class__(new_date, new_invoice_number, new_customer, new_invoiced_amount, new_invoiced_quantity)

    def __str__(self):
        return (f"Invoice(\n"
                f"  Date: {self.date}\n"
                f"  Invoice Number: {self.invoice_number}\n"
                f"  Customer: {self.customer}\n"
                f"  Invoiced Amount: {self.invoiced_amount}\n"
                f"  Invoiced Quantity: {self.invoiced_quantity}\n"
                f")")

invoice1 = Invoice(dt.date(2020, 1, 1), 73984, "John Wayne", 500.0, 2.0)
invoice2 = Invoice(dt.date(2020, 1, 12), 51341, "Michael Johnson", 125.0, 3.5)
invoice3 = Invoice(dt.date(2020, 1, 31), 43210, "Stuart Smith", 1200.0, 1.0)

invoice4 = invoice1 + invoice2 +  invoice3
invioce5 = invoice4 - invoice2
invoice6 = invoice1 + invoice1 - invoice3
print(invoice4)
print(invioce5)
print(invoice6)


# %%
