from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os

app = Flask(__name__)
CORS(app)

# Basic HMRC Tax Rules (2024/25 as example)
PERSONAL_ALLOWANCE = 12570
BASIC_RATE = 0.20
HIGHER_RATE = 0.40
ADDITIONAL_RATE = 0.45

BASIC_THRESHOLD = 50270
HIGHER_THRESHOLD = 125140


def calculate_tax(income):
    tax = 0
    if income <= PERSONAL_ALLOWANCE:
        return 0

    taxable = income - PERSONAL_ALLOWANCE

    if income <= BASIC_THRESHOLD:
        tax = taxable * BASIC_RATE
    elif income <= HIGHER_THRESHOLD:
        tax = ((BASIC_THRESHOLD - PERSONAL_ALLOWANCE) * BASIC_RATE) + ((income - BASIC_THRESHOLD) * HIGHER_RATE)
    else:
        tax = ((BASIC_THRESHOLD - PERSONAL_ALLOWANCE) * BASIC_RATE) + \
              ((HIGHER_THRESHOLD - BASIC_THRESHOLD) * HIGHER_RATE) + \
              ((income - HIGHER_THRESHOLD) * ADDITIONAL_RATE)
    return round(tax, 2)


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file)
        else:
            return jsonify({'error': 'Unsupported file format'}), 400

        required_columns = {'Income', 'Expenses'}
        if not required_columns.issubset(df.columns):
            return jsonify({'error': f'Missing required columns: {required_columns - set(df.columns)}'}), 400

        # Assume file has columns: Income, Expenses
        total_income = df['Income'].sum()
        expenses = df['Expenses'].sum()
        taxable_income = max(total_income - expenses, 0)
        tax_owed = calculate_tax(taxable_income)

        return jsonify({
            'total_income': float(total_income),
            'expenses': float(expenses),
            'taxable_income': float(taxable_income),
            'tax_owed': float(tax_owed)
        })
    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True)
