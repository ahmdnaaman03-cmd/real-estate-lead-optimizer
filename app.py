import streamlit as st
import pandas as pd
import requests
import re
import io

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Real Estate Lead Optimizer",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- BRANDING & STYLES ---
st.markdown("""
    <style>
    /* Custom Theme Colors */
    :root {
        --primary-color: #1E3A8A;
        --secondary-color: #3B82F6;
        --accent-color: #F59E0B;
    }
    
    .main {
        background-color: #F3F4F6;
    }
    
    /* Button Styling */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3.2em;
        background-color: #1E3A8A;
        color: white;
        font-weight: 600;
        border: none;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background-color: #3B82F6;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    /* Card-like containers */
    div[data-testid="stMetricValue"] {
        font-size: 24px;
        color: #1E3A8A;
    }
    
    /* Footer Styling */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #FFFFFF;
        color: #1F2937;
        text-align: center;
        padding: 12px;
        font-weight: 700;
        border-top: 2px solid #E5E7EB;
        z-index: 1000;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.05);
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if 'is_paid' not in st.session_state:
    st.session_state.is_paid = False
if 'df' not in st.session_state:
    st.session_state.df = None
if 'payment_token' not in st.session_state:
    st.session_state.payment_token = None
if 'order_id' not in st.session_state:
    st.session_state.order_id = None
if 'total_price' not in st.session_state:
    st.session_state.total_price = 0

# --- HELPER FUNCTIONS ---

def calculate_price(num_rows):
    """Calculate dynamic price based on number of leads."""
    price_per_row = 0.05
    min_charge = 50.0
    total = num_rows * price_per_row
    return max(min_charge, total)

def get_paymob_token(api_key):
    """Step 1: Auth Token Request"""
    url = "https://accept.paymob.com/api/auth/tokens"
    payload = {"api_key": api_key}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json().get("token")
    except Exception as e:
        st.error(f"Authentication Error: {str(e)}")
        return None

def register_order(token, amount_cents):
    """Step 2: Order Registration"""
    url = "https://accept.paymob.com/api/ecommerce/orders"
    payload = {
        "auth_token": token,
        "delivery_needed": "false",
        "amount_cents": str(amount_cents),
        "currency": "EGP",
        "items": []
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json().get("id")
    except Exception as e:
        st.error(f"Order Registration Error: {str(e)}")
        return None

def get_payment_key(token, order_id, integration_id, amount_cents):
    """Step 3: Payment Key Generation"""
    url = "https://accept.paymob.com/api/acceptance/payment_keys"
    payload = {
        "auth_token": token,
        "amount_cents": str(amount_cents),
        "expiration": 3600,
        "order_id": order_id,
        "billing_data": {
            "apartment": "NA",
            "email": "customer@example.com",
            "floor": "NA",
            "first_name": "Lead",
            "street": "NA",
            "building": "NA",
            "phone_number": "NA",
            "shipping_method": "NA",
            "postal_code": "NA",
            "city": "NA",
            "country": "NA",
            "last_name": "Optimizer",
            "state": "NA"
        },
        "currency": "EGP",
        "integration_id": integration_id
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json().get("token")
    except Exception as e:
        st.error(f"Payment Key Error: {str(e)}")
        return None

def verify_transaction(transaction_id, token):
    """Verify transaction status using Paymob API"""
    url = f"https://accept.paymob.com/api/acceptance/transactions/{transaction_id}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            # Paymob returns success: True/False and pending: True/False
            if data.get("success") is True and data.get("pending") is False:
                return True
        return False
    except Exception as e:
        st.error(f"Verification Error: {str(e)}")
        return False

def generate_sample_data():
    """Generate a sample CSV for testing purposes."""
    data = {
        "Name": ["Ahmed Ali", "Sara Hassan", "John Doe", "VIP Test 1", "VIP Test 2", "Duplicate Test"],
        "Phone": ["01012345678", "01177788990", "01234567890", "01099912345", "01111111111", "01012345678"],
        "Location": ["التجمع", "New Cairo", "Sheikh Zayed", "التجمع الخامس", "Zayed", "New Cairo"]
    }
    return pd.DataFrame(data)

# --- MAIN APP INTERFACE ---

st.title("🏢 Real Estate Lead Optimizer")
st.subheader("Transform your raw lead data into high-value assets")

# Sidebar for Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    paymob_api_key = st.text_input("Paymob API Key", type="password", help="Your Paymob Admin API Key")
    paymob_integration_id = st.text_input("Paymob Integration ID", help="The ID of your payment integration")
    paymob_iframe_id = st.text_input("Paymob Iframe ID", help="The ID of the iframe you want to use")
    
    st.divider()
    if st.button("📥 Download Sample Leads"):
        sample_df = generate_sample_data()
        csv = sample_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button("Download CSV", csv, "sample_leads.csv", "text/csv")
    
    st.divider()
    st.info("Upload your leads file to calculate pricing.")
    
    if st.session_state.is_paid:
        st.success("✅ System Unlocked")
        if st.button("Reset Payment (Debug)"):
            st.session_state.is_paid = False
            st.rerun()

# 1. File Upload Section
uploaded_file = st.file_uploader("Upload your leads (CSV or Excel)", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        st.session_state.df = df
        total_leads = len(df)
        total_price_egp = calculate_price(total_leads)
        st.session_state.total_price = total_price_egp
        
        st.success(f"✅ File uploaded successfully! Found **{total_leads}** leads.")
        
        # 2. Payment Section
        if not st.session_state.is_paid:
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Leads", total_leads)
            with col2:
                st.metric("Optimization Price", f"{total_price_egp:.2f} EGP")
            
            st.warning("💳 Payment Required to unlock cleaning and export features.")
            
            if st.button("🚀 Generate Payment Link"):
                if not paymob_api_key or not paymob_integration_id or not paymob_iframe_id:
                    st.error("⚠️ Please provide all Paymob configuration details in the sidebar.")
                else:
                    try:
                        with st.spinner("🔄 Establishing secure connection with Paymob..."):
                            token = get_paymob_token(paymob_api_key)
                            if token:
                                amount_cents = int(total_price_egp * 100)
                                order_id = register_order(token, amount_cents)
                                if order_id:
                                    payment_token = get_payment_key(token, order_id, paymob_integration_id, amount_cents)
                                    if payment_token:
                                        st.session_state.payment_token = payment_token
                                        checkout_url = f"https://accept.paymob.com/api/acceptance/iframes/{paymob_iframe_id}?payment_token={payment_token}"
                                        st.success("🔗 Payment link generated successfully!")
                                        st.markdown(f'''
                                            <a href="{checkout_url}" target="_blank" style="text-decoration: none;">
                                                <div style="width:100%; background-color:#10B981; color:white; text-align:center; padding:15px; border-radius:10px; font-weight:bold; cursor:pointer; font-size:18px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                                                    💳 Click Here to Pay {total_price_egp:.2f} EGP
                                                </div>
                                            </a>
                                            ''', unsafe_allow_html=True)
                                        st.info("💡 Note: After successful payment, please copy your Transaction ID and paste it below.")
                    except Exception as e:
                        st.error(f"❌ Payment Initialization Failed: {str(e)}")
            
            # Transaction Verification
            st.markdown("### Verify Payment")
            trans_id = st.text_input("Enter Transaction ID after payment")
            if st.button("Verify & Unlock"):
                if trans_id:
                    with st.spinner("Verifying..."):
                        # We need a token for verification. Use the one from state or re-auth
                        token = get_paymob_token(paymob_api_key)
                        if verify_transaction(trans_id, token):
                            st.session_state.is_paid = True
                            st.success("🎉 Payment Verified! Features Unlocked.")
                            st.rerun()
                        else:
                            st.error("Invalid Transaction ID or Payment not successful yet.")
                else:
                    st.warning("Please enter a Transaction ID.")

        # 3. Post-Payment Features
        if st.session_state.is_paid:
            st.markdown("---")
            st.header("🛠️ Lead Optimization Tools")
            
            # Feature tabs
            tab1, tab2, tab3, tab4 = st.tabs(["📊 Summary", "📱 Phone Standardizer", "🧹 Deduplication", "🌍 Location & Export"])
            
            with tab1:
                st.write("### Data Overview")
                st.write(df.head())
                # Add basic metrics
                c1, c2, c3 = st.columns(3)
                c1.metric("Total Rows", len(df))
                c2.metric("Total Columns", len(df.columns))
                # Check for phone column (case insensitive)
                phone_col = next((c for c in df.columns if 'phone' in c.lower() or 'mobile' in c.lower()), None)
                if phone_col:
                    dupes = df[phone_col].duplicated().sum()
                    c3.metric("Duplicate Phones", dupes)
                else:
                    c3.warning("No phone column detected.")

            # Get phone column
            phone_col = next((c for c in df.columns if 'phone' in c.lower() or 'mobile' in c.lower()), None)
            
            with tab2:
                st.write("### Phone Standardization & VIP Detection")
                if phone_col:
                    if st.button("Process & Classify Leads"):
                        def standardize_phone(phone):
                            phone = str(phone).strip()
                            # Remove non-numeric characters
                            digits = re.sub(r'\D', '', phone)
                            
                            # Handle Egyptian format
                            # If it starts with 20, remove it and add 0
                            if digits.startswith('20') and len(digits) >= 12:
                                digits = '0' + digits[2:]
                            # If it starts with 0020, remove it and add 0
                            elif digits.startswith('0020') and len(digits) >= 14:
                                digits = '0' + digits[4:]
                            # If it's 10 digits and starts with 1, add 0
                            elif len(digits) == 10 and digits.startswith('1'):
                                digits = '0' + digits
                            
                            # Final check: Egyptian mobile numbers are 11 digits starting with 01
                            if len(digits) == 11 and digits.startswith('01'):
                                return digits
                            return digits # Return as is if it doesn't match standard Egyptian mobile

                        def classify_lead(phone):
                            phone = str(phone)
                            # VIP - Ultra: 3+ consecutive identical digits (e.g., 777)
                            if re.search(r'(\d)\1\1', phone):
                                return "VIP - Ultra"
                            
                            # VIP - Premium: Any single digit (excluding '0') repeating 5+ times non-consecutively
                            # We count each digit from 1-9
                            for d in "123456789":
                                if phone.count(d) >= 5:
                                    return "VIP - Premium"
                            
                            return "Standard"

                        df['Cleaned_Phone'] = df[phone_col].apply(standardize_phone)
                        df['Lead_Class'] = df['Cleaned_Phone'].apply(classify_lead)
                        st.session_state.df = df
                        st.success("Phones standardized and VIP classes assigned!")
                        st.dataframe(df[[phone_col, 'Cleaned_Phone', 'Lead_Class']].head(10))
                        
                        # Show stats
                        class_counts = df['Lead_Class'].value_counts()
                        st.bar_chart(class_counts)
                else:
                    st.error("No phone column detected. Please rename your phone column to 'phone' or 'mobile'.")

            with tab3:
                st.write("### Smart De-duplication")
                if phone_col:
                    keep_option = st.radio("Which record to keep?", ["First", "Last"])
                    if st.button("Remove Duplicates"):
                        original_len = len(df)
                        df = df.drop_duplicates(subset=[phone_col], keep=keep_option.lower())
                        st.session_state.df = df
                        st.success(f"Removed {original_len - len(df)} duplicates. Remaining: {len(df)}")
                else:
                    st.error("Cannot de-duplicate without a phone column.")

            with tab4:
                st.write("### Location Standardizer & Export")
                st.markdown("#### 🌍 Standardize Locations")
                location_col = st.selectbox("Select Location Column", df.columns)
                
                unique_locs = df[location_col].unique()
                st.write(f"Found {len(unique_locs)} unique variations.")
                
                with st.expander("Configure Replacements"):
                    st.write("Enter variations separated by commas to map to a standard name.")
                    mapping_text = st.text_area("Format: Standard Name = variation1, variation2", 
                                              placeholder="New Cairo = التجمع, التجمع الخامس, New Cairo")
                
                if st.button("Apply Standardization"):
                    if mapping_text:
                        mapping_dict = {}
                        for line in mapping_text.split('\n'):
                            if '=' in line:
                                standard, variations = line.split('=')
                                standard = standard.strip()
                                for var in variations.split(','):
                                    mapping_dict[var.strip()] = standard
                        
                        df[location_col] = df[location_col].replace(mapping_dict)
                        st.session_state.df = df
                        st.success("Location names unified!")
                    else:
                        st.warning("Please provide mapping configuration.")

                st.markdown("---")
                st.markdown("#### 📤 Secure Export")
                if 'Lead_Class' in df.columns:
                    filter_class = st.multiselect("Filter by Lead Class", df['Lead_Class'].unique(), default=df['Lead_Class'].unique())
                    export_df = df[df['Lead_Class'].isin(filter_class)]
                else:
                    export_df = df
                
                st.write(f"Exporting {len(export_df)} leads.")
                
                # Export to CSV with utf-8-sig for Excel compatibility
                csv_buffer = io.StringIO()
                export_df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
                st.download_button(
                    label="Download Optimized Leads (CSV)",
                    data=csv_buffer.getvalue(),
                    file_name="optimized_leads.csv",
                    mime="text/csv"
                )

    except Exception as e:
        st.error(f"Error processing file: {str(e)}")

else:
    st.info("👋 Welcome! Please upload your leads file to begin.")

# --- FOOTER ---
st.markdown('<div class="footer">Developed by Ahmed Saeed</div>', unsafe_allow_html=True)
