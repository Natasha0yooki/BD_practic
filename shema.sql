-- ============================================================
-- КРЕДИТНАЯ БД LENDING CLUB (ИСПРАВЛЕННАЯ ВЕРСИЯ)
-- PostgreSQL 14+
-- ============================================================

CREATE SCHEMA IF NOT EXISTS credit;
SET search_path TO credit, public;

-- 1. Справочник грейдов
CREATE TABLE loan_grade (
    grade CHAR(1) NOT NULL,
    sub_grade CHAR(2) NOT NULL,

    PRIMARY KEY (grade, sub_grade),

    CHECK (grade IN ('A','B','C','D','E','F','G')),
    CHECK (sub_grade IN (
        'A1','A2','A3','A4','A5',
        'B1','B2','B3','B4','B5',
        'C1','C2','C3','C4','C5',
        'D1','D2','D3','D4','D5',
        'E1','E2','E3','E4','E5',
        'F1','F2','F3','F4','F5',
        'G1','G2','G3','G4','G5'
    )),
    CHECK (LEFT(sub_grade, 1) = grade)
);

-- 2. Заявка на кредит (Центральная сущность)
CREATE TABLE loan_application (
    application_id BIGSERIAL PRIMARY KEY,
    loan_amnt NUMERIC(12,2) NOT NULL CHECK (loan_amnt > 0),
    term SMALLINT NOT NULL CHECK (term IN (36, 60)),
    purpose VARCHAR(50),
    title VARCHAR(200),
    application_type VARCHAR(20) CHECK (application_type IN ('Individual', 'Joint App')),
    issue_date DATE NOT NULL, -- месяц выдачи кредита
    description TEXT, -- переименовано из 'desc' (desc - зарезервированное слово)
    url TEXT
);

-- 3. Профиль заявителя (1:1 к заявке, так как member_id пуст)
CREATE TABLE applicant_profile (
    profile_id BIGSERIAL PRIMARY KEY,
    application_id BIGINT NOT NULL UNIQUE REFERENCES loan_application(application_id) ON DELETE CASCADE,
    emp_title VARCHAR(150),
    emp_length VARCHAR(20) CHECK (
        emp_length IN ('< 1 year', '1 year', '2 years', '3 years', '4 years', 
                       '5 years', '6 years', '7 years', '8 years', '9 years', '10+ years')
    ),
    home_ownership VARCHAR(20) CHECK (home_ownership IN ('RENT', 'OWN', 'MORTGAGE', 'OTHER', 'ANY', 'NONE')),
    annual_inc NUMERIC(12,2) CHECK (annual_inc >= 0), -- Разрешаем NULL
    verification_status VARCHAR(30) CHECK (verification_status IN ('Not Verified', 'Source Verified', 'Verified')),
    addr_state CHAR(2),
    zip_code VARCHAR(10)
);

-- 4. Кредитная история на момент подачи (1:1 к заявке)
CREATE TABLE credit_profile (
    credit_profile_id BIGSERIAL PRIMARY KEY,
    application_id BIGINT NOT NULL UNIQUE REFERENCES loan_application(application_id) ON DELETE CASCADE,
    dti NUMERIC(6,2) CHECK (dti >= 0),
    delinq_2yrs SMALLINT CHECK (delinq_2yrs >= 0),
    earliest_cr_line DATE,
    fico_range_low SMALLINT CHECK (fico_range_low BETWEEN 300 AND 850), -- проверить
    fico_range_high SMALLINT CHECK (fico_range_high BETWEEN 300 AND 850), -- проверить
    inq_last_6mths SMALLINT CHECK (inq_last_6mths >= 0),
    open_acc SMALLINT CHECK (open_acc >= 0),
    pub_rec SMALLINT CHECK (pub_rec >= 0),
    revol_bal NUMERIC(12,2) CHECK (revol_bal >= 0),
    revol_util NUMERIC(7,2) CHECK (revol_util >= 0),
    total_acc SMALLINT CHECK (total_acc >= 0),
    CHECK (
        fico_range_low IS NULL
        OR fico_range_high IS NULL
        OR fico_range_low <= fico_range_high
    )
);

-- 5. Выданный кредит
CREATE TABLE loan (
    loan_id BIGINT PRIMARY KEY, -- Берем из оригинального id датасета
    application_id BIGINT NOT NULL UNIQUE REFERENCES loan_application(application_id) ON DELETE RESTRICT,
    funded_amnt NUMERIC(12,2) NOT NULL CHECK (funded_amnt >= 0),
    funded_amnt_inv NUMERIC(12,2) CHECK (funded_amnt_inv >= 0),
    int_rate NUMERIC(5,2) CHECK (int_rate >= 0 AND int_rate <= 100),
    installment NUMERIC(10,2) CHECK (installment > 0),
    grade CHAR(1) NOT NULL,
    sub_grade CHAR(2) NOT NULL,
    loan_status VARCHAR(50) NOT NULL,
    pymnt_plan CHAR(1) DEFAULT 'n' CHECK (pymnt_plan IN ('y', 'n')),
    initial_list_status CHAR(1) CHECK (initial_list_status IN ('f', 'w')),
    FOREIGN KEY (grade, sub_grade) REFERENCES loan_grade(grade, sub_grade)
);

-- 6. Показатели обслуживания долга (Агрегаты, 1:0..1 к кредиту)
CREATE TABLE loan_performance (
    performance_id BIGSERIAL PRIMARY KEY,
    loan_id BIGINT NOT NULL UNIQUE REFERENCES loan(loan_id) ON DELETE CASCADE,
    total_pymnt NUMERIC(12,2), -- Разрешаем NULL, 0 не равен NULL
    total_pymnt_inv NUMERIC(12,2),
    total_rec_prncp NUMERIC(12,2),
    total_rec_int NUMERIC(12,2),
    total_rec_late_fee NUMERIC(10,2),
    recoveries NUMERIC(12,2),
    collection_recovery_fee NUMERIC(10,2),
    last_pymnt_d DATE,
    last_pymnt_amnt NUMERIC(10,2),
    next_pymnt_d DATE,
    out_prncp NUMERIC(12,2), -- Остаток основного долга
    out_prncp_inv NUMERIC(12,2),
    last_credit_pull_d DATE,
    last_fico_range_low SMALLINT CHECK (last_fico_range_low BETWEEN 300 AND 850),
    last_fico_range_high SMALLINT CHECK (last_fico_range_high BETWEEN 300 AND 850),
    CHECK (last_fico_range_low <= last_fico_range_high)
);

-- 7. Финансовые трудности (Hardship)
CREATE TABLE hardship (
    hardship_id BIGSERIAL PRIMARY KEY,
    loan_id BIGINT NOT NULL UNIQUE REFERENCES loan(loan_id) ON DELETE CASCADE,
    hardship_flag CHAR(1) CHECK (hardship_flag IN ('Y', 'N')),
    hardship_type VARCHAR(50),
    hardship_reason VARCHAR(50),
    hardship_status VARCHAR(50),
    hardship_amount NUMERIC(12,2),
    hardship_start_date DATE,
    hardship_end_date DATE,
    hardship_dpd SMALLINT CHECK (hardship_dpd >= 0),
    hardship_loan_status VARCHAR(50),
    hardship_payoff_balance_amount NUMERIC(12,2) CHECK (hardship_payoff_balance_amount >= 0),
    hardship_last_payment_amount NUMERIC(12,2) CHECK (hardship_last_payment_amount >= 0),
    hardship_length SMALLINT CHECK (hardship_length >= 0),
    deferral_term SMALLINT CHECK (deferral_term >= 0),
    payment_plan_start_date DATE,
    orig_projected_additional_accrued_interest NUMERIC(12,2) CHECK ( orig_projected_additional_accrued_interest >= 0),
    CHECK (hardship_end_date IS NULL OR hardship_start_date IS NULL OR hardship_end_date >= hardship_start_date)
);

-- 8. Урегулирование задолженности (Settlement)
CREATE TABLE settlement (
    settlement_id BIGSERIAL PRIMARY KEY,
    loan_id BIGINT NOT NULL UNIQUE REFERENCES loan(loan_id) ON DELETE CASCADE,
    debt_settlement_flag CHAR(1) CHECK (debt_settlement_flag IN ('Y', 'N')),
    settlement_status VARCHAR(50),
    settlement_date DATE,
    settlement_amount NUMERIC(12,2) CHECK (settlement_amount >= 0),
    settlement_percentage NUMERIC(5,2) CHECK (settlement_percentage BETWEEN 0 AND 100),
    settlement_flag_date DATE,
    settlement_term SMALLINT CHECK (settlement_term > 0)
);

-- 9. Отклоненные заявки (Отдельный файл rejected CSV)
CREATE TABLE rejected_application (
    rejected_id BIGSERIAL PRIMARY KEY,
    amount_requested NUMERIC(12,2) CHECK (amount_requested > 0),
    application_date DATE,
    loan_title VARCHAR(200),
    risk_score NUMERIC(8,2), -- В rejected Risk_Score бывает с плавающей точкой
    dti NUMERIC(8,2),
    zip_code VARCHAR(10),
    state CHAR(2),
    emp_length VARCHAR(20),
    policy_code SMALLINT
);


-- =========================================
-- ИНДЕКСЫ
-- =========================================

-- Аналитика по статусам кредита
CREATE INDEX idx_loan_status ON loan(loan_status);
-- Аналитика по кредитным грейдам
CREATE INDEX idx_loan_grade ON loan(grade, sub_grade);
-- Поиск кредитов по дате выдачи
CREATE INDEX idx_application_issue_d ON loan_application(issue_date);
-- BRIN для больших таблиц с хронологической загрузкой
CREATE INDEX idx_application_issue_brin ON loan_application USING BRIN(issue_date);
CREATE INDEX idx_rejected_date_brin ON rejected_application USING BRIN(application_date);
-- Аналитика отклонённых заявок
CREATE INDEX idx_rejected_risk_score ON rejected_application(risk_score);
CREATE INDEX idx_rejected_state ON rejected_application(state);