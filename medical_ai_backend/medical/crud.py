from fastapi import HTTPException
from db_generation.db_conn import get_connection
from medical.auth import hash_password, verify_password


# =====================================================
# REGISTER ORGANIZATION
# =====================================================

def create_organization(data):

    conn = get_connection()
    cur = conn.cursor()

    # =====================================================
    # CREATE ORGANIZATION
    # =====================================================

    organization_query = """
    INSERT INTO medical_oltp.organizations
    (
        organization_name,
        organization_type,
        gst_number,
        corporate_email,
        corporate_phone
    )
    VALUES (%s, %s, %s, %s, %s)
    RETURNING organization_id;
    """

    cur.execute(
        organization_query,
        (
            data.name,
            data.org_type,
            data.gst_number,
            data.email,
            data.phone
        )
    )

    organization_id = cur.fetchone()[0]

    # =====================================================
    # IF INDEPENDENT → AUTO CREATE STORE
    # =====================================================

    store_id = None

    if data.org_type.lower() == "independent":

        store_query = """
        INSERT INTO medical_oltp.stores
        (
            organization_id,
            store_name,
            gst_number,
            phone_number,
            email,
            city,
            state,
            country,
            pincode
        )
        VALUES
        (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING store_id;
        """

        cur.execute(
            store_query,
            (
                organization_id,
                data.name,
                data.gst_number,
                data.phone,
                data.email,
                data.city,
                data.state,
                data.country,
                data.postal_code
            )
        )

        store_id = cur.fetchone()[0]

    conn.commit()

    cur.close()
    conn.close()

    return {
        "message": "Organization created",
        "organization_id": organization_id,
        "store_id": store_id
    }


# =====================================================
# REGISTER STORE
# =====================================================

def create_store(data):

    conn = get_connection()
    cur = conn.cursor()

    query = """
    INSERT INTO medical_oltp.stores
    (
        organization_id,
        store_name,
        drug_license_number,
        gst_number,
        phone_number,
        email,
        address_line_1,
        address_line_2,
        city,
        state,
        country,
        pincode
    )
    VALUES
    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    RETURNING store_id;
    """

    cur.execute(
        query,
        (
            data.organisation_id,
            data.name,
            data.drug_license_number,
            data.gst_number,
            data.phone,
            data.email,
            data.address_line1,
            data.address_line2,
            data.city,
            data.state,
            data.country,
            data.postal_code
        )
    )

    store_id = cur.fetchone()[0]

    conn.commit()

    cur.close()
    conn.close()

    return {
        "message": "Store created",
        "store_id": store_id
    }


# =====================================================
# REGISTER USER
# =====================================================

def create_user(data):

    conn = get_connection()
    cur = conn.cursor()

    hashed_password = hash_password(data.password)

    user_query = """
    INSERT INTO medical_oltp.users
    (
        full_name,
        username,
        email,
        phone_number,
        password_hash
    )
    VALUES (%s, %s, %s, %s, %s)
    RETURNING user_id;
    """

    cur.execute(
        user_query,
        (
            data.full_name,
            data.username,
            data.email,
            data.phone_number,
            hashed_password
        )
    )

    user_id = cur.fetchone()[0]

    store_user_query = """
    INSERT INTO medical_oltp.store_users
    (
        store_id,
        user_id,
        role
    )
    VALUES (%s, %s, %s);
    """

    cur.execute(
        store_user_query,
        (
            data.store_id,
            user_id,
            data.role
        )
    )

    conn.commit()

    cur.close()
    conn.close()

    return {
        "message": "User registered successfully",
        "user_id": user_id
    }


# =====================================================
# LOGIN USER
# =====================================================

def login_user(data):

    conn = get_connection()
    cur = conn.cursor()

    query = """
    SELECT
        user_id,
        full_name,
        username,
        email,
        password_hash
    FROM medical_oltp.users
    WHERE username = %s;
    """

    cur.execute(query, (data.username,))

    user = cur.fetchone()

    cur.close()
    conn.close()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username"
        )

    user_id, full_name, username, email, hashed_password = user


    if not verify_password(
        data.password,
        hashed_password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid password"
        )

    return {
        "message": "Login successful",
        "user_id": user_id,
        "name": full_name,
        "email": email,
        "username": username
    }