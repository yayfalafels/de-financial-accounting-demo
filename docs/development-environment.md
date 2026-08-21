# Development Environment Design
## Banking Data Ingestion & Reconciliation Assignment

### Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Option 1: Docker-Based Spark Environment (Recommended)](#option-1-docker-based-spark-environment-recommended)
- [Option 2: AWS Glue Alternative](#option-2-aws-glue-alternative)
- [Mock Data Generation](#mock-data-generation)
- [Closed-Loop Feedback System](#closed-loop-feedback-system)
- [VS Code & AI Agent Integration](#vs-code--ai-agent-integration)
- [Quick Start Guide](#quick-start-guide)

---

## Overview

This document describes a complete development environment for implementing and validating the Data Analyst assignment. The design enables:

- **Local development** using Docker containers with Apache Spark pre-installed
- **Scalable mock data generation** simulating banking datasets (25M+ records)
- **Closed-loop validation** with automated reconciliation feedback
- **AI agent-native** workflow integrated with VS Code terminal
- **Rapid iteration** without cloud infrastructure dependencies (optional cloud fallback)

### Key Design Principles

1. **Reproducibility**: All environments defined as code
2. **Cost-effective**: Local Docker primary, AWS optional
3. **AI-Friendly**: Terminal-driven, scriptable, Copilot/Claude agent-compatible
4. **Scalable**: Mock data volumes match production scenarios
5. **Automated Feedback**: Reconciliation results drive corrective actions

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Development Workflow                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  VS Code Terminal (Local or Remote)                          │
│        ↓                                                      │
│  AI Agent (Copilot/Claude) Scripts Generation                │
│        ↓                                                      │
│  ┌─────────────────────────────────────────────────────┐     │
│  │           Docker Compose Orchestration              │     │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────┐  │     │
│  │  │ Spark Master │  │ PostgreSQL   │  │ Python  │  │     │
│  │  │ + Workers    │  │ (Metadata)   │  │ Worker  │  │     │
│  │  └──────────────┘  └──────────────┘  └─────────┘  │     │
│  │        ↓                  ↓                ↓        │     │
│  │  Parquet/Delta Data    Control DB    Transform    │     │
│  └─────────────────────────────────────────────────────┘     │
│        ↓                                                      │
│  Validation & Reconciliation Layer                           │
│  (SQL, PySpark Notebooks, Python Scripts)                    │
│        ↓                                                      │
│  Feedback Loop                                               │
│  (Metrics, Exception Reports, Data Quality Scores)           │
│        ↓                                                      │
│  VS Code Output / Dashboard                                  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Core Technologies

| ID | Component      | Technology               | Version | Purpose    |
|----|----------------|--------------------------|---------|------------|
| 1  | Compute        | Apache Spark             | 3.5+    | [P1]       |
| 2  | Orchestration  | Docker / Docker Compose  | Latest  | [P2]       |
| 3  | Storage        | Delta Lake / Parquet     | Latest  | [P3]       |
| 4  | Metadata       | PostgreSQL               | 15+     | [P4]       |
| 5  | Notebooks      | Jupyter / Databricks     | Community | [P5]      |
| 6  | Python         | Python                   | 3.11+   | [P6]       |
| 7  | Scripting      | Bash / Python            | Latest  | [P7]       |
| 8  | Monitoring     | Custom Python + logs     | N/A     | [P8]       |

**Technology Purpose References:**
- [P1] SQL, PySpark for large-scale data processing
- [P2] Container orchestration and management
- [P3] Data format for Lake House architecture
- [P4] Reconciliation control tables and metadata
- [P5] Interactive notebook-based analysis environments
- [P6] PySpark, data generation, workflow automation
- [P7] Workflow automation and scripting
- [P8] Reconciliation metrics and monitoring

### Optional Extensions

- **VS Code Extensions**: Jupyter, Python, Docker, Databricks
- **AI Integration**: Copilot/Claude prompts for script generation
- **BI (Optional)**: Power BI Desktop or Metabase for dashboards
- **Cloud (Optional)**: AWS Glue for larger-scale testing

---

## Option 1: Docker-Based Spark Environment (Recommended)

### 1.1 Prerequisites

```bash
- Docker Desktop (v4.0+) or Docker Engine + Docker Compose
- VS Code (with Docker extension recommended)
- Git
- 8GB RAM minimum, 50GB disk space
- Python 3.11+ (for local script generation)
```

### 1.2 Directory Structure

```
ambition-take-home/
├── docs/
│   ├── assignment.md
│   └── development-environment.md (this file)
├── docker/
│   ├── Dockerfile.spark          # Custom Spark image
│   ├── Dockerfile.postgres       # PostgreSQL image
│   ├── docker-compose.yml        # Orchestration
│   └── entrypoint.sh             # Spark startup
├── data/
│   ├── mock/                     # Generated mock data
│   │   ├── source/
│   │   ├── bronze/
│   │   └── staging/
│   ├── schemas/                  # Data definitions
│   │   ├── source_schema.json
│   │   ├── bronze_schema.json
│   │   └── reference_schema.json
│   └── samples/                  # Sample datasets for testing
├── notebooks/
│   ├── assessment1_profiling.ipynb
│   ├── assessment2_gl_reconciliation.ipynb
│   └── assessment3_regulatory.ipynb
├── scripts/
│   ├── setup_dev_env.sh          # Initial setup
│   ├── generate_mock_data.py     # Mock data generator
│   ├── run_reconciliation.py     # Validation runner
│   ├── feedback_loop.py          # Metrics & monitoring
│   └── utils/                    # Helper functions
│       ├── data_generators.py
│       ├── reconciliation_rules.py
│       └── control_tables.py
├── results/
│   ├── reconciliation_reports/
│   ├── exception_tables/
│   └── metrics.json
└── README.md
```

### 1.3 Docker Compose Configuration

Create `docker/docker-compose.yml`:

```yaml
version: '3.8'

services:
  spark-master:
    build:
      context: .
      dockerfile: Dockerfile.spark
    container_name: spark-master
    environment:
      SPARK_MODE: master
      SPARK_RPC_AUTHENTICATION_ENABLED: no
      SPARK_RPC_ENCRYPTION_ENABLED: no
      SPARK_LOCAL_STORAGE_ENCRYPTION_ENABLED: no
      SPARK_SSL_ENABLED: no
      SPARK_USER: spark
    ports:
      - "7077:7077"        # Spark Master port
      - "8080:8080"        # Spark UI
      - "4040:4040"        # Spark Application UI
    volumes:
      - ./data:/data
      - ./notebooks:/notebooks
      - ./scripts:/scripts
    networks:
      - spark-network

  spark-worker-1:
    build:
      context: .
      dockerfile: Dockerfile.spark
    container_name: spark-worker-1
    environment:
      SPARK_MODE: worker
      SPARK_MASTER_URL: spark://spark-master:7077
      SPARK_WORKER_MEMORY: 2G
      SPARK_WORKER_CORES: 2
      SPARK_USER: spark
    depends_on:
      - spark-master
    ports:
      - "8081:8081"
    volumes:
      - ./data:/data
      - ./notebooks:/notebooks
    networks:
      - spark-network

  spark-worker-2:
    build:
      context: .
      dockerfile: Dockerfile.spark
    container_name: spark-worker-2
    environment:
      SPARK_MODE: worker
      SPARK_MASTER_URL: spark://spark-master:7077
      SPARK_WORKER_MEMORY: 2G
      SPARK_WORKER_CORES: 2
      SPARK_USER: spark
    depends_on:
      - spark-master
    ports:
      - "8082:8082"
    volumes:
      - ./data:/data
      - ./notebooks:/notebooks
    networks:
      - spark-network

  postgres:
    image: postgres:15-alpine
    container_name: postgres-metadata
    environment:
      POSTGRES_DB: reconciliation_db
      POSTGRES_USER: analyst
      POSTGRES_PASSWORD: secure_password_123
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init_postgres.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - spark-network

  jupyter:
    build:
      context: .
      dockerfile: Dockerfile.spark
    container_name: jupyter-notebook
    command: >
      bash -c "pip install jupyter && 
               jupyter notebook --ip=0.0.0.0 --port=8888 --no-browser 
               --allow-root --NotebookApp.token='' 
               --NotebookApp.password=''"
    depends_on:
      - spark-master
      - postgres
    ports:
      - "8888:8888"
    volumes:
      - ./notebooks:/notebooks
      - ./data:/data
      - ./scripts:/scripts
    networks:
      - spark-network
    working_dir: /notebooks

networks:
  spark-network:
    driver: bridge

volumes:
  postgres_data:
```

### 1.4 Dockerfile for Spark

Create `docker/Dockerfile.spark`:

```dockerfile
FROM bitnami/spark:3.5.0

USER root

# Install Python development tools and pip
RUN apt-get update && apt-get install -y \
    python3-dev \
    python3-pip \
    postgresql-client \
    git \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Install required Python packages
RUN pip install \
    pyspark==3.5.0 \
    pandas==2.1.0 \
    numpy==1.24.0 \
    psycopg2-binary==2.9.0 \
    delta-spark==3.0.0 \
    faker==19.0.0 \
    sqlalchemy==2.0.0 \
    jupyter==1.0.0 \
    jupyterlab==4.0.0 \
    plotly==5.17.0 \
    pandas-gbq==0.19.0

# Create working directories
RUN mkdir -p /data /notebooks /scripts
RUN chmod -R 777 /data /notebooks /scripts

WORKDIR /

CMD ["/opt/bitnami/spark/bin/spark-class", "org.apache.spark.deploy.master.Master"]
```

### 1.5 Initial PostgreSQL Schema

Create `scripts/init_postgres.sql`:

```sql
-- Reconciliation Control Tables
CREATE SCHEMA IF NOT EXISTS reconciliation;

-- Batch Control Table
CREATE TABLE reconciliation.batch_control (
    batch_id SERIAL PRIMARY KEY,
    batch_date DATE NOT NULL,
    assessment_id INT,
    source_count BIGINT,
    bronze_count BIGINT,
    expected_count BIGINT,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Reconciliation Results
CREATE TABLE reconciliation.reconciliation_results (
    result_id SERIAL PRIMARY KEY,
    batch_id INT REFERENCES reconciliation.batch_control(batch_id),
    dimension VARCHAR(100),
    source_value DECIMAL(20,2),
    target_value DECIMAL(20,2),
    variance DECIMAL(20,2),
    variance_pct DECIMAL(10,4),
    reconciliation_status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Exception Log
CREATE TABLE reconciliation.exceptions (
    exception_id SERIAL PRIMARY KEY,
    batch_id INT REFERENCES reconciliation.batch_control(batch_id),
    record_key VARCHAR(255),
    issue_type VARCHAR(100),
    source_value TEXT,
    target_value TEXT,
    severity VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Data Quality Metrics
CREATE TABLE reconciliation.data_quality_metrics (
    metric_id SERIAL PRIMARY KEY,
    batch_id INT REFERENCES reconciliation.batch_control(batch_id),
    metric_name VARCHAR(100),
    metric_value DECIMAL(10,4),
    threshold_value DECIMAL(10,4),
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit Trail
CREATE TABLE reconciliation.audit_trail (
    audit_id SERIAL PRIMARY KEY,
    batch_id INT REFERENCES reconciliation.batch_control(batch_id),
    action VARCHAR(255),
    details TEXT,
    actor VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_batch_date ON reconciliation.batch_control(batch_date);
CREATE INDEX idx_exception_type ON reconciliation.exceptions(issue_type);
CREATE INDEX idx_metric_name ON reconciliation.data_quality_metrics(metric_name);
```

---

## 2. Mock Data Generation

### 2.1 Data Generator Strategy

Create `scripts/generate_mock_data.py`:

```python
"""
Mock Data Generator for Banking Dataset
Generates realistic data matching Assessment scenarios
"""

import sys
from datetime import datetime, timedelta
from pyspark.sql import SparkSession
from pyspark.sql.types import *
from pyspark.sql.functions import *
from faker import Faker
import random

class BankingDataGenerator:
    def __init__(self, spark_session, num_records=25000000):
        self.spark = spark_session
        self.num_records = num_records
        self.fake = Faker()
        
    def generate_source_transactions(self):
        """Generate Assessment 1: Source Transaction Data"""
        # Define schema
        schema = StructType([
            StructField("transaction_id", StringType(), False),
            StructField("account_id", StringType(), False),
            StructField("transaction_date", DateType(), False),
            StructField("posting_date", DateType(), False),
            StructField("transaction_type", StringType(), False),
            StructField("currency_code", StringType(), False),
            StructField("transaction_amount", DecimalType(20,2), False),
            StructField("local_currency_amount", DecimalType(20,2), False),
            StructField("exchange_rate", DecimalType(10,6), False),
            StructField("branch_code", StringType(), False),
            StructField("product_code", StringType(), False),
            StructField("source_system", StringType(), False),
            StructField("ingestion_file", StringType(), False),
            StructField("source_extract_ts", TimestampType(), False)
        ])
        
        def generate_row():
            """Generator function for individual rows"""
            txn_date = datetime.now() - timedelta(days=random.randint(0, 30))
            post_date = txn_date + timedelta(days=random.randint(0, 3))
            amount = round(random.uniform(100, 1000000), 2)
            fx_rate = round(random.uniform(0.8, 1.5), 6)
            
            return (
                f"TXN-{self.fake.uuid4()}",
                f"ACC-{random.randint(1000000, 9999999)}",
                txn_date.date(),
                post_date.date(),
                random.choice(["DEBIT", "CREDIT"]),
                random.choice(["SGD", "USD", "EUR", "GBP", "JPY"]),
                amount,
                round(amount * fx_rate, 2),
                fx_rate,
                f"BR{random.randint(100, 999)}",
                random.choice(["SAVINGS", "CURRENT", "INVESTMENT", "LOAN"]),
                "COREBANKING",
                f"source_extract_{random.randint(1, 50)}.dat",
                datetime.now()
            )
        
        # Generate RDD and convert to DataFrame
        rdd = self.spark.sparkContext.parallelize(
            [generate_row() for _ in range(self.num_records)]
        )
        df = self.spark.createDataFrame(rdd, schema=schema)
        
        return df
    
    def generate_gl_transactions(self):
        """Generate Assessment 2: GL Transaction Data"""
        # Implementation for GL transactions
        pass
    
    def generate_payment_transactions(self):
        """Generate Assessment 3: Payment Transaction Data"""
        # Implementation for payment transactions
        pass
    
    def save_mock_data(self, df, path, format="parquet"):
        """Save generated data"""
        df.write.mode("overwrite").format(format).save(path)
        print(f"Saved {df.count()} records to {path}")

def main():
    spark = SparkSession.builder \
        .appName("MockDataGenerator") \
        .master("spark://spark-master:7077") \
        .getOrCreate()
    
    generator = BankingDataGenerator(spark, num_records=25000000)
    
    print("Generating source transaction data...")
    source_txns = generator.generate_source_transactions()
    generator.save_mock_data(source_txns, "/data/mock/source/transactions")
    
    print("Mock data generation complete!")

if __name__ == "__main__":
    main()
```

### 2.2 Data Quality Issues (Intentional)

Insert realistic issues into mock data:

```python
def introduce_data_quality_issues(df):
    """Intentionally add issues for discovery"""
    
    # 1. Duplicate records (1% of data)
    duplicates = df.sample(fraction=0.01)
    df_with_dupes = df.union(duplicates)
    
    # 2. Null values in critical fields (0.5%)
    df_with_nulls = df_with_dupes.withColumn(
        "currency_code",
        when(rand() < 0.005, None).otherwise(col("currency_code"))
    )
    
    # 3. Invalid amounts (0.2%)
    df_with_invalid = df_with_nulls.withColumn(
        "transaction_amount",
        when(rand() < 0.002, -abs(col("transaction_amount")))
            .otherwise(col("transaction_amount"))
    )
    
    # 4. Posting date before transaction date (0.1%)
    df_with_late = df_with_invalid.withColumn(
        "posting_date",
        when(rand() < 0.001, date_sub(col("transaction_date"), 5))
            .otherwise(col("posting_date"))
    )
    
    # 5. FX rate mismatch (0.3%)
    df_with_fx = df_with_late.withColumn(
        "local_currency_amount",
        when(rand() < 0.003, round(col("transaction_amount") * 1.2, 2))
            .otherwise(col("local_currency_amount"))
    )
    
    return df_with_fx
```

---

## 3. Closed-Loop Feedback System

### 3.1 Reconciliation Runner

Create `scripts/run_reconciliation.py`:

```python
"""
Reconciliation Runner - Executes validation checks and captures feedback
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from datetime import datetime
import psycopg2
import json

class ReconciliationRunner:
    def __init__(self, spark, pg_conn):
        self.spark = spark
        self.pg_conn = pg_conn
        
    def run_assessment_1(self, batch_id):
        """Assessment 1: Source-to-Bronze Reconciliation"""
        
        # Load source and bronze
        source_df = self.spark.read.parquet("/data/mock/source/transactions")
        bronze_df = self.spark.read.parquet("/data/mock/bronze/transactions")
        
        # Batch-level reconciliation
        source_count = source_df.count()
        bronze_count = bronze_df.count()
        
        source_amount = source_df.agg(sum("transaction_amount")).collect()[0][0]
        bronze_amount = bronze_df.agg(sum("transaction_amount")).collect()[0][0]
        
        variance = bronze_amount - source_amount if source_amount else 0
        variance_pct = (variance / source_amount * 100) if source_amount else 0
        
        # Store results
        self.store_reconciliation_result(
            batch_id=batch_id,
            dimension="Batch Level",
            source_value=source_count,
            target_value=bronze_count,
            variance=variance,
            variance_pct=variance_pct
        )
        
        return {
            "source_count": source_count,
            "bronze_count": bronze_count,
            "variance": variance,
            "variance_pct": variance_pct,
            "status": "PASS" if variance_pct < 0.1 else "FAIL"
        }
    
    def store_reconciliation_result(self, batch_id, dimension, source_value, 
                                     target_value, variance, variance_pct):
        """Store results in PostgreSQL"""
        cursor = self.pg_conn.cursor()
        status = "PASS" if abs(variance_pct) < 0.1 else "WARNING" if abs(variance_pct) < 1 else "FAIL"
        
        cursor.execute("""
            INSERT INTO reconciliation.reconciliation_results
            (batch_id, dimension, source_value, target_value, variance, variance_pct, reconciliation_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (batch_id, dimension, source_value, target_value, variance, variance_pct, status))
        
        self.pg_conn.commit()
        cursor.close()

def main():
    spark = SparkSession.builder \
        .appName("ReconciliationRunner") \
        .master("spark://spark-master:7077") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .getOrCreate()
    
    # Connect to PostgreSQL
    pg_conn = psycopg2.connect(
        host="postgres",
        database="reconciliation_db",
        user="analyst",
        password="secure_password_123"
    )
    
    runner = ReconciliationRunner(spark, pg_conn)
    
    # Create batch
    cursor = pg_conn.cursor()
    cursor.execute("""
        INSERT INTO reconciliation.batch_control (batch_date, assessment_id, status)
        VALUES (%s, %s, %s) RETURNING batch_id
    """, (datetime.now().date(), 1, "RUNNING"))
    batch_id = cursor.fetchone()[0]
    pg_conn.commit()
    
    # Run assessments
    result = runner.run_assessment_1(batch_id)
    
    print(json.dumps(result, indent=2, default=str))
    
    pg_conn.close()

if __name__ == "__main__":
    main()
```

### 3.2 Feedback Loop & Metrics

Create `scripts/feedback_loop.py`:

```python
"""
Closed-Loop Feedback System
Monitors reconciliation and triggers corrective actions
"""

import psycopg2
import json
from datetime import datetime

class FeedbackLoop:
    def __init__(self, pg_conn):
        self.pg_conn = pg_conn
        
    def check_reconciliation_status(self, batch_id):
        """Retrieve and analyze reconciliation status"""
        cursor = self.pg_conn.cursor()
        
        cursor.execute("""
            SELECT 
                dimension,
                variance,
                variance_pct,
                reconciliation_status
            FROM reconciliation.reconciliation_results
            WHERE batch_id = %s
            ORDER BY abs(variance_pct) DESC
        """, (batch_id,))
        
        results = cursor.fetchall()
        cursor.close()
        
        return results
    
    def generate_report(self, batch_id):
        """Generate comprehensive reconciliation report"""
        cursor = self.pg_conn.cursor()
        
        cursor.execute("""
            SELECT 
                bc.batch_id,
                bc.batch_date,
                COUNT(DISTINCT rr.dimension) as dimension_count,
                SUM(CASE WHEN rr.reconciliation_status = 'PASS' THEN 1 ELSE 0 END) as pass_count,
                SUM(CASE WHEN rr.reconciliation_status = 'WARNING' THEN 1 ELSE 0 END) as warning_count,
                SUM(CASE WHEN rr.reconciliation_status = 'FAIL' THEN 1 ELSE 0 END) as fail_count
            FROM reconciliation.batch_control bc
            LEFT JOIN reconciliation.reconciliation_results rr ON bc.batch_id = rr.batch_id
            WHERE bc.batch_id = %s
            GROUP BY bc.batch_id, bc.batch_date
        """, (batch_id,))
        
        report = cursor.fetchone()
        cursor.close()
        
        return {
            "batch_id": report[0],
            "batch_date": str(report[1]),
            "dimensions_tested": report[2],
            "passed": report[3],
            "warnings": report[4],
            "failed": report[5],
            "overall_status": "PASS" if report[5] == 0 else "FAIL"
        }
    
    def trigger_action(self, batch_id, action_type):
        """Trigger corrective action based on feedback"""
        actions = {
            "INVESTIGATE": "Manual investigation required",
            "RERUN": "Re-run reconciliation with adjusted parameters",
            "NOTIFY": "Notify stakeholders of data quality issues",
            "QUARANTINE": "Quarantine batch pending investigation"
        }
        
        cursor = self.pg_conn.cursor()
        cursor.execute("""
            INSERT INTO reconciliation.audit_trail (batch_id, action, actor)
            VALUES (%s, %s, %s)
        """, (batch_id, actions.get(action_type, "Unknown action"), "automated_system"))
        
        self.pg_conn.commit()
        cursor.close()
        
        return {"action": action_type, "message": actions.get(action_type)}

def main():
    pg_conn = psycopg2.connect(
        host="postgres",
        database="reconciliation_db",
        user="analyst",
        password="secure_password_123"
    )
    
    feedback = FeedbackLoop(pg_conn)
    
    # Example usage
    batch_id = 1  # Latest batch
    report = feedback.generate_report(batch_id)
    print("\n=== RECONCILIATION REPORT ===")
    print(json.dumps(report, indent=2))
    
    # Trigger actions based on status
    if report["overall_status"] == "FAIL":
        feedback.trigger_action(batch_id, "INVESTIGATE")
    
    pg_conn.close()

if __name__ == "__main__":
    main()
```

---

## 4. VS Code & AI Agent Integration

### 4.1 Copilot Prompt Templates

Create `.vscode/copilot-prompts.md`:

```markdown
# Banking Assignment - Copilot Prompts

## Scenario 1: Generate Mock Data
"Generate Spark/PySpark code to create 25M records of banking transaction data 
with fields: transaction_id, account_id, transaction_date, posting_date, 
transaction_type, currency_code, transaction_amount, local_currency_amount, 
exchange_rate, branch_code, product_code. Include realistic values for banking 
domain and save as Parquet to /data/mock/source/transactions."

## Scenario 2: Profile Data Quality
"Write Spark SQL queries to profile transaction data and identify:
- Duplicate transaction IDs
- Null percentages in critical fields
- Invalid transaction types
- Negative or zero amounts
- Records where posting_date < transaction_date
- FX conversion mismatches (local_currency_amount != transaction_amount * exchange_rate)"

## Scenario 3: Build Reconciliation Logic
"Create a PySpark reconciliation framework comparing Source and Bronze tables at:
- Batch level (count, amounts)
- Dimensional level (by currency, branch, product)
- Record level (joins, exception categorization)
Output should include a reconciliation_results table with variance calculations."

## Scenario 4: Investigate Variance
"Given:
- Source count: 25,017,842
- Bronze count: 24,998,131
- Missing: 19,711 records
- Files created near midnight
- Some timestamps in UTC, others in SGD

Write Spark queries to:
1. Identify missing records by source file
2. Analyze timestamp issues
3. Quantify financial impact
4. Recommend remediation"

## Scenario 5: GL Reconciliation
"Build GL reconciliation logic comparing Finance.gl_balance with 
bronze.finance_transactions. Validate:
- Opening Balance + Debits - Credits = Closing Balance
- Transactions posted to expected GL accounts
- Effective date mapping
- Duplicate entries"

## Scenario 6: Create Dashboard Design
"Design a Power BI dashboard mockup for reconciliation monitoring with:
- KPIs: Source records, Bronze records, Reconciliation rate, Variance
- Visuals: Status by date, exceptions trend, variance by entity, DQ issues
- Filters: Date, legal entity, currency, payment type"
```

### 4.2 VS Code Tasks

Create `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Setup Development Environment",
      "type": "shell",
      "command": "bash",
      "args": ["scripts/setup_dev_env.sh"],
      "presentation": {
        "echo": true,
        "reveal": "always"
      },
      "problemMatcher": []
    },
    {
      "label": "Start Docker Containers",
      "type": "shell",
      "command": "docker-compose",
      "args": ["-f", "docker/docker-compose.yml", "up", "-d"],
      "presentation": {
        "reveal": "always"
      },
      "problemMatcher": []
    },
    {
      "label": "Generate Mock Data",
      "type": "shell",
      "command": "docker",
      "args": [
        "exec",
        "spark-master",
        "spark-submit",
        "/scripts/generate_mock_data.py"
      ],
      "presentation": {
        "reveal": "always"
      },
      "problemMatcher": []
    },
    {
      "label": "Run Reconciliation",
      "type": "shell",
      "command": "docker",
      "args": [
        "exec",
        "spark-master",
        "python3",
        "/scripts/run_reconciliation.py"
      ],
      "presentation": {
        "reveal": "always"
      },
      "problemMatcher": []
    },
    {
      "label": "View Feedback Report",
      "type": "shell",
      "command": "docker",
      "args": [
        "exec",
        "spark-master",
        "python3",
        "/scripts/feedback_loop.py"
      ],
      "presentation": {
        "reveal": "always"
      },
      "problemMatcher": []
    },
    {
      "label": "Access Spark UI",
      "type": "shell",
      "command": "open",
      "args": ["http://localhost:8080"]
    },
    {
      "label": "Access Jupyter",
      "type": "shell",
      "command": "open",
      "args": ["http://localhost:8888"]
    },
    {
      "label": "Stop Containers",
      "type": "shell",
      "command": "docker-compose",
      "args": ["-f", "docker/docker-compose.yml", "down"]
    }
  ]
}
```

### 4.3 AI Agent Workflow Script

Create `scripts/ai_agent_workflow.py`:

```python
"""
AI Agent Workflow Handler
Enables Copilot/Claude to trigger tasks from terminal
"""

import sys
import subprocess
import json
from datetime import datetime

class AgentWorkflow:
    def __init__(self):
        self.commands = {
            "setup": self.setup_environment,
            "generate": self.generate_mock_data,
            "reconcile": self.run_reconciliation,
            "feedback": self.get_feedback,
            "status": self.get_status,
            "investigate": self.investigate_variance
        }
    
    def setup_environment(self, *args):
        """Initialize development environment"""
        print("Setting up development environment...")
        subprocess.run(["docker-compose", "-f", "docker/docker-compose.yml", "up", "-d"])
        subprocess.run(["bash", "scripts/setup_dev_env.sh"])
        return {"status": "success", "message": "Environment ready"}
    
    def generate_mock_data(self, *args):
        """Generate mock data"""
        print("Generating mock banking data...")
        result = subprocess.run([
            "docker", "exec", "spark-master",
            "spark-submit", "/scripts/generate_mock_data.py"
        ], capture_output=True, text=True)
        return {"status": "success" if result.returncode == 0 else "error", 
                "output": result.stdout}
    
    def run_reconciliation(self, *args):
        """Execute reconciliation"""
        print("Running reconciliation checks...")
        result = subprocess.run([
            "docker", "exec", "spark-master",
            "python3", "/scripts/run_reconciliation.py"
        ], capture_output=True, text=True)
        return json.loads(result.stdout) if result.returncode == 0 else {"error": result.stderr}
    
    def get_feedback(self, *args):
        """Get feedback loop report"""
        print("Fetching reconciliation feedback...")
        result = subprocess.run([
            "docker", "exec", "spark-master",
            "python3", "/scripts/feedback_loop.py"
        ], capture_output=True, text=True)
        return {"feedback": result.stdout}
    
    def get_status(self, *args):
        """Get system status"""
        return {
            "timestamp": datetime.now().isoformat(),
            "containers": subprocess.run(
                ["docker", "ps", "--format", "json"],
                capture_output=True, text=True
            ).stdout
        }
    
    def investigate_variance(self, *args):
        """Investigate reconciliation variance"""
        if len(args) < 1:
            return {"error": "Batch ID required"}
        
        batch_id = args[0]
        print(f"Investigating variance for batch {batch_id}...")
        # Implementation here
        return {"batch_id": batch_id, "status": "investigating"}
    
    def execute(self, command, *args):
        """Execute command"""
        if command in self.commands:
            return self.commands[command](*args)
        else:
            return {"error": f"Unknown command: {command}"}

def main():
    if len(sys.argv) < 2:
        print("Usage: python ai_agent_workflow.py <command> [args]")
        print("Commands: setup, generate, reconcile, feedback, status, investigate")
        sys.exit(1)
    
    agent = AgentWorkflow()
    command = sys.argv[1]
    args = sys.argv[2:] if len(sys.argv) > 2 else []
    
    result = agent.execute(command, *args)
    print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    main()
```

---

## Option 2: AWS Glue Alternative

### 2.1 When to Use AWS Glue

- Local Docker reaches resource limits (> 100M records)
- Need true distributed processing across multiple nodes
- Integration with AWS data lake infrastructure
- Enterprise managed services requirements

### 2.2 AWS Glue Setup

```bash
# Create Glue job for mock data generation
aws glue create-job \
  --name banking-mock-data-generator \
  --role arn:aws:iam::ACCOUNT:role/GlueServiceRole \
  --command Name=glueetl,ScriptLocation=s3://bucket/scripts/generate_mock_data.py \
  --max-capacity 10 \
  --worker-type G.2X \
  --number-of-workers 10

# Create Glue job for reconciliation
aws glue create-job \
  --name banking-reconciliation-runner \
  --role arn:aws:iam::ACCOUNT:role/GlueServiceRole \
  --command Name=pythonshell,ScriptLocation=s3://bucket/scripts/run_reconciliation.py
```

### 2.3 AWS Infrastructure as Code (Terraform)

```hcl
# terraform/main.tf

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# S3 Bucket for data
resource "aws_s3_bucket" "data_bucket" {
  bucket = "banking-assignment-data-${data.aws_caller_identity.current.account_id}"
}

# RDS PostgreSQL for metadata
resource "aws_db_instance" "reconciliation_db" {
  identifier      = "banking-reconciliation-db"
  engine          = "postgres"
  engine_version  = "15.4"
  instance_class  = "db.t3.micro"
  allocated_storage = 20
  db_name         = "reconciliation_db"
  username        = "analyst"
  password        = random_password.db_password.result
  skip_final_snapshot = true
}

# Glue Catalog Database
resource "aws_glue_catalog_database" "banking_db" {
  name = "banking_database"
}

# Lambda for orchestration
resource "aws_lambda_function" "reconciliation_trigger" {
  filename      = "lambda/reconciliation_handler.zip"
  function_name = "banking-reconciliation-trigger"
  role          = aws_iam_role.lambda_role.arn
  handler       = "index.handler"
  runtime       = "python3.11"
}
```

---

## 5. Quick Start Guide

### 5.1 One-Command Setup (Docker)

```bash
# Clone repository
git clone <repo-url>
cd ambition-take-home

# Run complete setup
bash scripts/setup_dev_env.sh

# Start all services
docker-compose -f docker/docker-compose.yml up -d

# Generate mock data
docker exec spark-master spark-submit /scripts/generate_mock_data.py

# Run reconciliation
docker exec spark-master python3 /scripts/run_reconciliation.py

# View results
docker exec spark-master python3 /scripts/feedback_loop.py
```

### 5.2 VS Code Integration

```
1. Open /workspace/ in VS Code
2. Install extensions: Docker, Jupyter, Python
3. Run "Tasks: Run Task" → "Setup Development Environment"
4. Monitor progress in VS Code terminal
5. Access Jupyter at http://localhost:8888
6. Access Spark UI at http://localhost:8080
7. Start coding assessment solutions in notebooks/
```

### 5.3 AI Agent Workflow

```bash
# Via Copilot in VS Code terminal:
python scripts/ai_agent_workflow.py setup
python scripts/ai_agent_workflow.py generate
python scripts/ai_agent_workflow.py reconcile
python scripts/ai_agent_workflow.py feedback

# View logs:
docker logs spark-master
docker logs postgres-metadata
docker logs jupyter-notebook
```

---

## 6. Monitoring & Debugging

### 6.1 Health Checks

```bash
# Check all containers
docker-compose -f docker/docker-compose.yml ps

# View Spark UI
open http://localhost:8080

# Check Jupyter
open http://localhost:8888

# Query PostgreSQL directly
docker exec postgres-metadata psql -U analyst -d reconciliation_db \
  -c "SELECT * FROM reconciliation.batch_control ORDER BY created_at DESC LIMIT 5;"

# View Spark logs
docker logs spark-master | tail -100
```

### 6.2 Troubleshooting

| ID | Issue                        | Cause                    | Solution           |
|----|------------------------------|--------------------------|---------------------|
| 1  | Out of memory                | Too many partitions      | [S1]                |
| 2  | Spark connection failure     | Master not ready         | [S2]                |
| 3  | PostgreSQL connection error  | Password mismatch        | [S3]                |
| 4  | Notebook kernel dies         | PySpark misconfiguration | [S4]                |

**Troubleshooting Solutions:**
- [S1] Reduce `num_records` parameter or increase Docker memory allocation
- [S2] Wait 30 seconds after `docker-compose up` for Master initialization
- [S3] Verify credentials in docker-compose.yml match environment
- [S4] Restart jupyter container: `docker restart jupyter-notebook`

---

## 7. Implementation Checklist

- [ ] Clone repository
- [ ] Install Docker & Docker Compose
- [ ] Run `setup_dev_env.sh`
- [ ] Verify all containers running: `docker ps`
- [ ] Generate mock data
- [ ] Run Assessment 1 reconciliation
- [ ] Check results in PostgreSQL
- [ ] Create Jupyter notebooks for analysis
- [ ] Implement Assessment 2 & 3 solutions
- [ ] Generate Power BI dashboard mockup
- [ ] Document findings

---

## 8. References

- **Apache Spark**: https://spark.apache.org/docs/latest/
- **Databricks**: https://docs.databricks.com/
- **Delta Lake**: https://docs.delta.io/
- **Docker**: https://docs.docker.com/
- **Faker Library**: https://faker.readthedocs.io/
- **PostgreSQL**: https://www.postgresql.org/docs/

---

## Appendix: Environment Variables

```bash
# docker/.env
SPARK_MASTER_URL=spark://spark-master:7077
SPARK_WORKER_MEMORY=2G
SPARK_WORKER_CORES=2
POSTGRES_USER=analyst
POSTGRES_PASSWORD=secure_password_123
POSTGRES_DB=reconciliation_db
JUPYTER_PORT=8888
SPARK_UI_PORT=8080
DATA_PATH=/data
SCRIPTS_PATH=/scripts
NOTEBOOKS_PATH=/notebooks
```

