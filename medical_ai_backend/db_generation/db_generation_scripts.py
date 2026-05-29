import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

DB_NAME = "lit_db"
DB_USER = "postgres"
DB_PASSWORD = "123456"
DB_HOST = "localhost"
DB_PORT = "5432"


# ======================================================
# DATABASE CREATION
# ======================================================

def create_database():

    conn = psycopg2.connect(
        dbname="postgres",
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    cur = conn.cursor()

    cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")

    if not cur.fetchone():
        cur.execute(f"CREATE DATABASE {DB_NAME}")
        print(f"Database '{DB_NAME}' created.")
    else:
        print(f"Database '{DB_NAME}' already exists.")

    cur.close()
    conn.close()


# ======================================================
# MAIN SCHEMA SETUP
# ======================================================

def setup_schema():

    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

    cur = conn.cursor()

    # ======================================================
    # SCHEMAS
    # ======================================================

    cur.execute("CREATE SCHEMA IF NOT EXISTS medical_oltp;")
    cur.execute("CREATE SCHEMA IF NOT EXISTS medical_olap;")

    # ======================================================
    # ENUMS
    # ======================================================

    enum_queries = [

        """
        DO $$
        BEGIN
            CREATE TYPE medical_oltp.organization_type_enum AS ENUM (
                'chain',
                'independent',
                'franchise'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        """,

        """
        DO $$
        BEGIN
            CREATE TYPE medical_oltp.store_role_enum AS ENUM (
                'owner',
                'manager',
                'pharmacist',
                'cashier',
                'delivery_staff',
                'auditor',
                'admin'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        """,

        """
        DO $$
        BEGIN
            CREATE TYPE medical_oltp.inventory_movement_enum AS ENUM (
                'purchase',
                'sale',
                'return_in',
                'return_out',
                'damage',
                'expiry',
                'adjustment',
                'transfer_in',
                'transfer_out'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        """,

        """
        DO $$
        BEGIN
            CREATE TYPE medical_oltp.payment_method_enum AS ENUM (
                'cash',
                'upi',
                'card',
                'wallet',
                'credit'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        """,

        """
        DO $$
        BEGIN
            CREATE TYPE medical_oltp.digital_order_source_enum AS ENUM (
                'mobile_app',
                'website',
                'whatsapp',
                'phone_order',
                'partner_platform',
                'telegram',
                'instagram',
                'facebook',
                'qr_scan',
                'api_order'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        """,

        """
        DO $$
        BEGIN
            CREATE TYPE medical_oltp.digital_rx_order_status_enum AS ENUM (
                'pending',
                'rx_uploaded',
                'rx_verified',
                'awaiting_pharmacist_review',
                'awaiting_stock_confirmation',
                'confirmed',
                'packed',
                'ready_for_dispatch',
                'out_for_delivery',
                'delivered',
                'partially_dispensed',
                'not_dispensed',
                'cancelled',
                'rejected',
                'expired',
                'refunded'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        """
    ]

    for query in enum_queries:
        cur.execute(query)

    # ======================================================
    # ORGANIZATIONS
    # ======================================================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS medical_oltp.organizations (

        organization_id BIGSERIAL PRIMARY KEY,

        organization_name VARCHAR(255) NOT NULL,

        organization_type medical_oltp.organization_type_enum,

        gst_number VARCHAR(100),

        corporate_phone VARCHAR(20),

        corporate_email VARCHAR(255),

        is_active BOOLEAN DEFAULT TRUE,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # ======================================================
    # STORES
    # ======================================================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS medical_oltp.stores (

        store_id BIGSERIAL PRIMARY KEY,

        organization_id BIGINT,

        store_name VARCHAR(255) NOT NULL,

        store_code VARCHAR(50) UNIQUE,

        drug_license_number VARCHAR(100) UNIQUE NOT NULL,

        gst_number VARCHAR(100),

        phone_number VARCHAR(20),

        email VARCHAR(255),

        address_line_1 TEXT,

        address_line_2 TEXT,

        city VARCHAR(100),

        state VARCHAR(100),

        country VARCHAR(100),

        pincode VARCHAR(20),

        latitude NUMERIC(10,7),

        longitude NUMERIC(10,7),

        operating_mode VARCHAR(50),

        is_active BOOLEAN DEFAULT TRUE,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (organization_id)
        REFERENCES medical_oltp.organizations(organization_id)
    );
    """)

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_stores_city
    ON medical_oltp.stores(city);
    """)

    # ======================================================
    # USERS
    # ======================================================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS medical_oltp.users (

        user_id BIGSERIAL PRIMARY KEY,

        full_name VARCHAR(255) NOT NULL,

        email VARCHAR(255) UNIQUE NOT NULL,

        phone_number VARCHAR(20) UNIQUE,

        password_hash TEXT NOT NULL,

        is_active BOOLEAN DEFAULT TRUE,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # ======================================================
    # STORE USERS
    # ======================================================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS medical_oltp.store_users (

        store_user_id BIGSERIAL PRIMARY KEY,

        store_id BIGINT NOT NULL,

        user_id BIGINT NOT NULL,

        role medical_oltp.store_role_enum NOT NULL,

        is_primary BOOLEAN DEFAULT FALSE,

        assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (store_id)
        REFERENCES medical_oltp.stores(store_id),

        FOREIGN KEY (user_id)
        REFERENCES medical_oltp.users(user_id)
    );
    """)

    # ======================================================
    # CUSTOMERS
    # ======================================================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS medical_oltp.customers (

        customer_id BIGSERIAL PRIMARY KEY,

        full_name VARCHAR(255),

        phone_number VARCHAR(20),

        gender VARCHAR(20),

        date_of_birth DATE,

        address TEXT,

        chronic_conditions TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # ======================================================
    # DOCTORS
    # ======================================================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS medical_oltp.doctors (

        doctor_id BIGSERIAL PRIMARY KEY,

        doctor_name VARCHAR(255) NOT NULL,

        specialization VARCHAR(255),

        clinic_name VARCHAR(255),

        phone_number VARCHAR(20),

        email VARCHAR(255),

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # ======================================================
    # PRODUCT CATEGORIES
    # ======================================================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS medical_oltp.product_categories (

        category_id BIGSERIAL PRIMARY KEY,

        category_name VARCHAR(255) UNIQUE NOT NULL,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # ======================================================
    # PRODUCT MASTER
    # ======================================================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS medical_oltp.product_master (

        product_id BIGSERIAL PRIMARY KEY,

        category_id BIGINT,

        product_name VARCHAR(255) NOT NULL,

        brand_name VARCHAR(255),

        generic_name VARCHAR(255),

        sku_code VARCHAR(100) UNIQUE,

        barcode VARCHAR(100),

        manufacturer_name VARCHAR(255),

        medicine_type VARCHAR(50),

        drug_schedule VARCHAR(20),

        salt_composition TEXT,

        strength VARCHAR(100),

        dosage_form VARCHAR(100),

        requires_cold_storage BOOLEAN DEFAULT FALSE,

        is_otc BOOLEAN DEFAULT FALSE,

        is_generic BOOLEAN DEFAULT FALSE,

        is_active BOOLEAN DEFAULT TRUE,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (category_id)
        REFERENCES medical_oltp.product_categories(category_id)
    );
    """)

    # ======================================================
    # PRODUCT PACKAGING
    # ======================================================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS medical_oltp.product_packaging (

        packaging_id BIGSERIAL PRIMARY KEY,

        product_id BIGINT NOT NULL,

        package_type VARCHAR(50),

        units_per_parent INTEGER,

        base_unit VARCHAR(50),

        barcode VARCHAR(100),

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (product_id)
        REFERENCES medical_oltp.product_master(product_id)
    );
    """)

    # ======================================================
    # VENDORS
    # ======================================================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS medical_oltp.vendors (

        vendor_id BIGSERIAL PRIMARY KEY,

        vendor_name VARCHAR(255) NOT NULL,

        contact_person VARCHAR(255),

        phone_number VARCHAR(20),

        gst_number VARCHAR(100),

        address TEXT,

        payment_terms TEXT,

        is_active BOOLEAN DEFAULT TRUE,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # ======================================================
    # INVENTORY BATCHES
    # ======================================================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS medical_oltp.inventory_batches (

        batch_id BIGSERIAL PRIMARY KEY,

        store_id BIGINT NOT NULL,

        product_id BIGINT NOT NULL,

        vendor_id BIGINT,

        batch_number VARCHAR(100) NOT NULL,

        batch_barcode VARCHAR(100),

        manufacture_date DATE,

        expiry_date DATE NOT NULL,

        mrp NUMERIC(12,2) NOT NULL,

        ptr NUMERIC(12,2),

        pts NUMERIC(12,2),

        purchase_price NUMERIC(12,2) NOT NULL,

        selling_price NUMERIC(12,2) NOT NULL,

        discount_percent NUMERIC(5,2) DEFAULT 0,

        opening_stock INTEGER DEFAULT 0,

        current_stock INTEGER DEFAULT 0,

        reorder_level INTEGER DEFAULT 0,

        safety_stock INTEGER DEFAULT 0,

        received_date DATE,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (store_id)
        REFERENCES medical_oltp.stores(store_id),

        FOREIGN KEY (product_id)
        REFERENCES medical_oltp.product_master(product_id),

        FOREIGN KEY (vendor_id)
        REFERENCES medical_oltp.vendors(vendor_id),

        UNIQUE(store_id, product_id, batch_number)
    );
    """)

    # ======================================================
    # SALES BILLS
    # ======================================================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS medical_oltp.sales_bills (

        bill_id BIGSERIAL PRIMARY KEY,

        store_id BIGINT,

        customer_id BIGINT,

        user_id BIGINT,

        bill_number VARCHAR(100) UNIQUE NOT NULL,

        subtotal NUMERIC(12,2) NOT NULL,

        discount_amount NUMERIC(12,2) DEFAULT 0,

        tax_amount NUMERIC(12,2) DEFAULT 0,

        total_amount NUMERIC(12,2) NOT NULL,

        payment_method medical_oltp.payment_method_enum,

        sales_channel VARCHAR(50),

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (store_id)
        REFERENCES medical_oltp.stores(store_id),

        FOREIGN KEY (customer_id)
        REFERENCES medical_oltp.customers(customer_id),

        FOREIGN KEY (user_id)
        REFERENCES medical_oltp.users(user_id)
    );
    """)

    # ======================================================
    # SALES BILL ITEMS
    # ======================================================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS medical_oltp.sales_bill_items (

        bill_item_id BIGSERIAL PRIMARY KEY,

        bill_id BIGINT,

        product_id BIGINT,

        batch_id BIGINT,

        quantity INTEGER NOT NULL,

        sold_unit VARCHAR(50),

        unit_price NUMERIC(12,2) NOT NULL,

        discount_amount NUMERIC(12,2) DEFAULT 0,

        total_price NUMERIC(12,2) NOT NULL,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (bill_id)
        REFERENCES medical_oltp.sales_bills(bill_id)
        ON DELETE CASCADE,

        FOREIGN KEY (product_id)
        REFERENCES medical_oltp.product_master(product_id),

        FOREIGN KEY (batch_id)
        REFERENCES medical_oltp.inventory_batches(batch_id)
    );
    """)

    # ======================================================
# PRESCRIPTIONS
# RX → DISPENSING WORKFLOW
# ======================================================

    cur.execute("""
CREATE TABLE IF NOT EXISTS medical_oltp.prescriptions (

    prescription_id BIGSERIAL PRIMARY KEY,

    store_id BIGINT,

    customer_id BIGINT NOT NULL,

    doctor_id BIGINT,

    prescription_number VARCHAR(100) UNIQUE,

    prescription_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    prescription_status VARCHAR(50) DEFAULT 'pending',

    diagnosis_notes TEXT,

    uploaded_rx_url TEXT,

    rx_source VARCHAR(50),

    valid_until DATE,

    created_by_user_id BIGINT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (store_id)
    REFERENCES medical_oltp.stores(store_id),

    FOREIGN KEY (customer_id)
    REFERENCES medical_oltp.customers(customer_id),

    FOREIGN KEY (doctor_id)
    REFERENCES medical_oltp.doctors(doctor_id),

    FOREIGN KEY (created_by_user_id)
    REFERENCES medical_oltp.users(user_id)
);
""")

# ======================================================
# PRESCRIPTION ITEMS
# ======================================================

    cur.execute("""
CREATE TABLE IF NOT EXISTS medical_oltp.prescription_items (

    prescription_item_id BIGSERIAL PRIMARY KEY,

    prescription_id BIGINT NOT NULL,

    product_id BIGINT NOT NULL,

    prescribed_quantity NUMERIC(10,2),

    prescribed_unit VARCHAR(50),

    dosage_instruction VARCHAR(255),

    frequency VARCHAR(100),

    duration_days INTEGER,

    route_of_administration VARCHAR(50),

    substitution_allowed BOOLEAN DEFAULT FALSE,

    remarks TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (prescription_id)
    REFERENCES medical_oltp.prescriptions(prescription_id)
    ON DELETE CASCADE,

    FOREIGN KEY (product_id)
    REFERENCES medical_oltp.product_master(product_id)
);
""")

# ======================================================
# RX DISPENSING
# Tracks actual medicine issued to customer
# ======================================================

    cur.execute("""
CREATE TABLE IF NOT EXISTS medical_oltp.rx_dispensing (

    dispensing_id BIGSERIAL PRIMARY KEY,

    prescription_item_id BIGINT NOT NULL,

    bill_id BIGINT,

    batch_id BIGINT,

    dispensed_product_id BIGINT NOT NULL,

    dispensed_quantity NUMERIC(10,2) NOT NULL,

    dispensed_by_user_id BIGINT,

    dispensed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    dispensing_status VARCHAR(50) DEFAULT 'dispensed',

    substitute_product_id BIGINT,

    pharmacist_notes TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (prescription_item_id)
    REFERENCES medical_oltp.prescription_items(prescription_item_id),

    FOREIGN KEY (bill_id)
    REFERENCES medical_oltp.sales_bills(bill_id),

    FOREIGN KEY (batch_id)
    REFERENCES medical_oltp.inventory_batches(batch_id),

    FOREIGN KEY (dispensed_product_id)
    REFERENCES medical_oltp.product_master(product_id),

    FOREIGN KEY (substitute_product_id)
    REFERENCES medical_oltp.product_master(product_id),

    FOREIGN KEY (dispensed_by_user_id)
    REFERENCES medical_oltp.users(user_id)
);
""")

# ======================================================
# INDEXES
# ======================================================

    cur.execute("""
CREATE INDEX IF NOT EXISTS idx_prescriptions_customer
ON medical_oltp.prescriptions(customer_id);
""")

    cur.execute("""
CREATE INDEX IF NOT EXISTS idx_prescriptions_store
ON medical_oltp.prescriptions(store_id);
""")

    cur.execute("""
CREATE INDEX IF NOT EXISTS idx_prescription_items_rx
ON medical_oltp.prescription_items(prescription_id);
""")

    cur.execute("""
CREATE INDEX IF NOT EXISTS idx_rx_dispensing_bill
ON medical_oltp.rx_dispensing(bill_id);
""")

    cur.execute("""
CREATE INDEX IF NOT EXISTS idx_rx_dispensing_batch
ON medical_oltp.rx_dispensing(batch_id);
""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS medical_oltp.rx_upsell_purchases (
        upsell_purchase_id BIGSERIAL PRIMARY KEY,
        bill_id BIGINT NOT NULL,
        customer_id BIGINT,
        prescription_id BIGINT,
        original_rx_product_id BIGINT,
        upsell_product_id BIGINT NOT NULL,
        quantity INTEGER DEFAULT 1,
        upsell_category VARCHAR(100),
        was_recommended BOOLEAN DEFAULT TRUE,
        recommended_by_user_id BIGINT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (bill_id) REFERENCES medical_oltp.sales_bills(bill_id),
        FOREIGN KEY (customer_id) REFERENCES medical_oltp.customers(customer_id),
        FOREIGN KEY (prescription_id) REFERENCES medical_oltp.prescriptions(prescription_id),
        FOREIGN KEY (original_rx_product_id) REFERENCES medical_oltp.product_master(product_id),
        FOREIGN KEY (upsell_product_id) REFERENCES medical_oltp.product_master(product_id),
        FOREIGN KEY (recommended_by_user_id) REFERENCES medical_oltp.users(user_id)
    );
    """)

    # ======================================================
    # COUNSELING PURCHASES
    # Products purchased after staff/user counseling
    # ======================================================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS medical_oltp.counseling_purchases (
        counseling_purchase_id BIGSERIAL PRIMARY KEY,
        bill_id BIGINT,
        customer_id BIGINT,
        counseled_by_user_id BIGINT NOT NULL,
        advised_product_id BIGINT NOT NULL,
        purchased_quantity INTEGER DEFAULT 1,
        counseling_type VARCHAR(100),
        counseling_notes TEXT,
        purchase_reason VARCHAR(255),
        was_purchased BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (bill_id) REFERENCES medical_oltp.sales_bills(bill_id),
        FOREIGN KEY (customer_id) REFERENCES medical_oltp.customers(customer_id),
        FOREIGN KEY (counseled_by_user_id) REFERENCES medical_oltp.users(user_id),
        FOREIGN KEY (advised_product_id) REFERENCES medical_oltp.product_master(product_id)
    );
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS medical_oltp.lab_test_referrals (
        referral_id BIGSERIAL PRIMARY KEY,
        store_id BIGINT,
        customer_id BIGINT NOT NULL,
        prescription_id BIGINT,
        doctor_id BIGINT,
        referred_by_user_id BIGINT,
        lab_name VARCHAR(255) NOT NULL,
        test_name VARCHAR(255) NOT NULL,
        test_category VARCHAR(100),
        referral_status VARCHAR(50),
        referral_fee NUMERIC(12,2) DEFAULT 0,
        lab_charge NUMERIC(12,2),
        referral_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (store_id) REFERENCES medical_oltp.stores(store_id),
        FOREIGN KEY (customer_id) REFERENCES medical_oltp.customers(customer_id),
        FOREIGN KEY (prescription_id) REFERENCES medical_oltp.prescriptions(prescription_id),
        FOREIGN KEY (doctor_id) REFERENCES medical_oltp.doctors(doctor_id),
        FOREIGN KEY (referred_by_user_id) REFERENCES medical_oltp.users(user_id)
    );
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS medical_oltp.customer_credit_accounts (

    credit_account_id BIGSERIAL PRIMARY KEY,

    customer_id BIGINT NOT NULL UNIQUE,

    total_credit_given NUMERIC(12,2) DEFAULT 0,

    total_credit_paid NUMERIC(12,2) DEFAULT 0,

    outstanding_balance NUMERIC(12,2) DEFAULT 0,

    credit_limit NUMERIC(12,2) DEFAULT 0,

    last_credit_date TIMESTAMP,

    last_payment_date TIMESTAMP,

    account_status VARCHAR(50) DEFAULT 'active',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (customer_id)
    REFERENCES medical_oltp.customers(customer_id)
);""")
    
    cur.execute("""
                CREATE TABLE IF NOT EXISTS medical_oltp.customer_credit_transactions (

    transaction_id BIGSERIAL PRIMARY KEY,

    credit_account_id BIGINT NOT NULL,

    bill_id BIGINT,

    transaction_type VARCHAR(50) NOT NULL,

    amount NUMERIC(12,2) NOT NULL,

    payment_method VARCHAR(50),

    notes TEXT,

    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    created_by_user_id BIGINT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (credit_account_id)
    REFERENCES medical_oltp.customer_credit_accounts(credit_account_id),

    FOREIGN KEY (bill_id)
    REFERENCES medical_oltp.sales_bills(bill_id),

    FOREIGN KEY (created_by_user_id)
    REFERENCES medical_oltp.users(user_id)
);""")
    






    cur.execute("""
    CREATE TABLE IF NOT EXISTS medical_oltp.digital_rx_orders (

    digital_rx_order_id BIGSERIAL PRIMARY KEY,

    store_id BIGINT NOT NULL,

    customer_id BIGINT,

    prescription_id BIGINT,

    sales_bill_id BIGINT,

    order_source medical_oltp.digital_order_source_enum NOT NULL,

    rx_uploaded BOOLEAN DEFAULT FALSE,

    uploaded_rx_url TEXT,

    consultation_required BOOLEAN DEFAULT FALSE,

    delivery_required BOOLEAN DEFAULT FALSE,

    order_status medical_oltp.digital_rx_order_status_enum,

    subtotal NUMERIC(12,2) DEFAULT 0,

    delivery_charges NUMERIC(12,2) DEFAULT 0,

    discount_amount NUMERIC(12,2) DEFAULT 0,

    total_amount NUMERIC(12,2) DEFAULT 0,

    ordered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    delivered_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (store_id)
    REFERENCES medical_oltp.stores(store_id),

    FOREIGN KEY (customer_id)
    REFERENCES medical_oltp.customers(customer_id),

    FOREIGN KEY (prescription_id)
    REFERENCES medical_oltp.prescriptions(prescription_id),

    FOREIGN KEY (sales_bill_id)
    REFERENCES medical_oltp.sales_bills(bill_id)
);""")

    conn.commit()

    cur.close()
    conn.close()

    print("Updated Medical POS schema setup completed successfully.")


if __name__ == "__main__":

    create_database()

    setup_schema()
