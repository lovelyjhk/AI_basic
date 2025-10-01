CREATE TABLE IF NOT EXISTS patients (
  id SERIAL PRIMARY KEY,
  patient_id VARCHAR(64) UNIQUE NOT NULL,
  name TEXT NOT NULL,
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS emr_records (
  id SERIAL PRIMARY KEY,
  patient_id VARCHAR(64) NOT NULL,
  record JSONB NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO patients (patient_id, name)
VALUES ('P001','Alice Kim')
ON CONFLICT (patient_id) DO NOTHING;

INSERT INTO emr_records (patient_id, record)
VALUES ('P001', '{"diagnosis":"Hypertension","meds":["DrugA"]}');
