import streamlit as st
import pandas as pd
import plotly.express as px
import re # For regular expressions in SKU parsing
import io # Import the io module for BytesIO
from datetime import datetime # For RFM analysis

# Import Firestore
from google.cloud import firestore
# Removed explicit import of Timestamp to avoid ImportErrors.
# We will convert firestore.Timestamp objects to strings for caching.
import json # For handling JSON credentials
import os # Import os to check environment variables for debugging

# Streamlit page configuration
st.set_page_config(
    layout="wide",
    page_title="Dashboard Analisis Data Data Ziel", # Translated
    initial_sidebar_state="expanded"
)

# Define Admin ID
ADMIN_USER_ID = "admin" # You can change this as needed

# --- Firestore Initialization ---
# Use st.secrets for secure credential management in Streamlit Cloud
@st.cache_resource
def get_firestore_client():
    """Initializes and returns a Firestore client."""
    print("Attempting to initialize Firestore client...") # Very early print for logs

    try:
        # DEBUG: Initial check for secrets availability
        if "firestore_credentials" in st.secrets:
            st.sidebar.info("Mendeteksi 'firestore_credentials' di st.secrets. Mencoba menginisialisasi Firestore...") # Translated
            print("Detected 'firestore_credentials' in st.secrets. Attempting Firestore initialization...") # Print to console log
            
            creds_json_string = st.secrets["firestore_credentials"]
            
            # DEBUG: Print the raw string content of the secret, its type, and length
            st.sidebar.info(f"Raw creds_json_string (first 200 chars): {creds_json_string[:200]}...") # Show first 200 chars
            print(f"Type of creds_json_string from st.secrets: {type(creds_json_string)}")
            print(f"Length of creds_json_string from st.secrets: {len(creds_json_string)}")
            
            try:
                # The private_key in the TOML file is now a single-line string with \\n escapes.
                # json.loads will correctly interpret \\n as \n.
                credentials = json.loads(creds_json_string)
                
                # DEBUG: Print the keys of the parsed dictionary
                print(f"Keys in parsed credentials dictionary: {credentials.keys()}")
                st.sidebar.info(f"Keys in parsed credentials: {list(credentials.keys())}")

                # Explicitly check for the missing keys for debugging purposes
                if "token_uri" not in credentials:
                    st.sidebar.error("DEBUG: 'token_uri' is MISSING in parsed credentials.")
                if "client_email" not in credentials:
                    st.sidebar.error("DEBUG: 'client_email' is MISSING in parsed credentials.")

                # The private_key must be the exact PEM string, including BEGIN/END headers and newlines.
                # We will only strip leading/trailing whitespace from the entire private_key string.
                # REMOVED .strip() from private_key as it might cause 'Incorrect padding' error
                if "private_key" in credentials and isinstance(credentials["private_key"], str):
                    # credentials["private_key"] = credentials["private_key"].strip() # REMOVED THIS LINE
                    # Added debug print for private_key length
                    print(f"Private key length after parsing (no strip): {len(credentials['private_key'])}. First 50 chars: {credentials['private_key'][:50]}...")
                
                # DEBUG: Check if project_id is present in the parsed credentials
                if "project_id" in credentials:
                    st.sidebar.info(f"Project ID terdeteksi: {credentials['project_id']}") # Translated
                    print(f"Project ID detected from credentials: {credentials['project_id']}") # Print to console log
                else:
                    st.sidebar.warning("Kunci 'project_id' tidak ditemukan dalam kredensial Firestore setelah parsing.") # Translated
                    print("Warning: 'project_id' key not found in Firestore credentials after parsing.") # Print to console log
                    st.sidebar.error("Pastikan 'project_id' ada di kredensial Firestore Anda. Ini penting untuk koneksi.") # Translated

                db = firestore.Client.from_service_account_info(credentials)
                st.sidebar.success("Terhubung ke Firestore menggunakan st.secrets.") # Translated
                print("Successfully connected to Firestore using st.secrets.") # Print to console log
                return db
            except json.JSONDecodeError as e_json:
                st.sidebar.error(f"Gagal mengurai JSON kredensial Firestore. Pastikan formatnya benar. Error: {e_json}") # Translated
                st.sidebar.error(f"Kredensial yang gagal diurai (awal): {creds_json_string[:200]}...") # Show beginning of problematic string
                print(f"JSON Decode Error: {e_json}. Problematic credentials start: {creds_json_string[:200]}...") # Print to console log
                st.sidebar.error("Ini mungkin disebabkan oleh format JSON yang salah di st.secrets['firestore_credentials']. Periksa kembali pemformatan, terutama karakter khusus seperti newline.") # Translated
                return None
            except Exception as e_creds_parse:
                st.sidebar.error(f"Kesalahan tak terduga saat memproses kredensial Firestore: {e_creds_parse}") # Translated
                print(f"Unexpected error during credential processing: {e_creds_parse}") # Print to console log
                st.sidebar.error("Pastikan kredensial akun layanan Anda valid dan Firestore API diaktifkan di Google Cloud Console.") # Translated
                return None
        else:
            st.sidebar.warning("Tidak ada 'firestore_credentials' di st.secrets. Mencoba koneksi default Firestore.") # Translated
            print("Warning: 'firestore_credentials' not found in st.secrets. Attempting default Firestore connection.") # Print to console log
            
            # Additional debug: Check if GOOGLE_APPLICATION_CREDENTIALS env var is set
            if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
                st.sidebar.info("GOOGLE_APPLICATION_CREDENTIALS environment variable DITEMUKAN.") # Translated
                print(f"GOOGLE_APPLICATION_CREDENTIALS env var found: {os.environ['GOOGLE_APPLICATION_CREDENTIALS']}") # Print to console log
            else:
                st.sidebar.info("GOOGLE_APPLICATION_CREDENTIALS environment variable TIDAK DITEMUKAN.") # Translated
                print("GOOGLE_APPLICATION_CREDENTIALS env var NOT found.") # Translated
                st.sidebar.warning("Jika Anda tidak menggunakan st.secrets, pastikan variabel lingkungan GOOGLE_APPLICATION_CREDENTIALS Anda diatur dengan benar.") # Translated

            # Attempt to get project ID from default credentials if available
            try:
                from google.auth import default
                _, project_id = default()
                if project_id:
                    st.sidebar.info(f"Project ID terdeteksi dari kredensial default: {project_id}") # Translated
                    print(f"Project ID detected from default credentials: {project_id}") # Print to console log
                else:
                    st.sidebar.warning("Tidak dapat mendeteksi Project ID dari kredensial default.") # Translated
            except Exception as e_default_creds:
                st.sidebar.warning(f"Gagal mendeteksi Project ID dari kredensial default: {e_default_creds}") # Translated
                print(f"Failed to detect Project ID from default credentials: {e_default_creds}") # Print to console log

            db = firestore.Client() # Assumes GOOGLE_APPLICATION_CREDENTIALS env var is set or running on GCP
            return db
    except Exception as e:
        st.sidebar.error(f"Gagal menginisialisasi Firestore: {e}") # Translated
        print(f"Critical error initializing Firestore: {e}") # Print to console log
        st.sidebar.error("Ini mungkin disebabkan oleh masalah koneksi umum atau Firestore API tidak diaktifkan untuk proyek Anda. Periksa Google Cloud Console.") # Translated
        return None

db = get_firestore_client()

# --- Helper Function for Cleaning Financial Strings ---
def clean_financial_string(s):
    """
    Cleans strings representing financial values for conversion to float.
    Handles Indonesian/European format (dot thousands, comma decimals)
    and American format (comma thousands, dot decimals).
    """
    if pd.isna(s):
        return 0.0
    
    # If it's already a number, return it directly
    if isinstance(s, (int, float)):
        return float(s)

    s = str(s).strip()
    s = s.replace('Rp', '').replace(' ', '') # Remove currency symbols and spaces

    # Check if comma is the decimal separator (Indonesian/European format)
    # This is assumed if a comma exists and appears after all dots, or only a comma exists
    if ',' in s and (s.rfind(',') > s.rfind('.')):
        s = s.replace('.', '') # Remove all dots (thousands separator)
        s = s.replace(',', '.') # Replace comma (decimal separator) with dot
    else:
        # Assume dot is the decimal separator (American format) or no separator
        # Remove all commas (thousands separator)
        s = s.replace(',', '')
        # The dot will be left and handled by float() as the decimal separator
    
    try:
        return float(s)
    except ValueError:
        return 0.0 # Return 0.0 if conversion fails

# --- Function to Load Data ---
@st.cache_data
def load_sku_master(file_uploader):
    """
    Loads SKU master data from the uploaded Excel file.
    This file is expected to have a single sheet with columns: 'CODE', 'ARTI', 'JENIS'.
    """
    # Initialize sku_decoder as a dictionary of dictionaries
    # These keys must match the expected values in the 'JENIS' column after normalization.
    sku_decoder = {
        'CATEGORY': {},
        'SUB_CATEGORY': {},
        'SEASON': {},
        'WARNA': {},
        'UKURAN': {},
        'TAHUN PRODUKSI': {},
        'SINGKATAN_NAMA_PRODUK': {},
        'DEFFECT': {} 
    }
    
    # Mapping to normalize 'JENIS' values from the Excel file to consistent internal keys
    # This is important if there are variations in spelling in the 'JENIS' column of the Excel file
    # Keys of this map will be normalized (uppercase, no spaces) for robust lookup.
    jenis_normalization_map_raw = {
        'CATEGORY': 'CATEGORY',
        'SUB CATEGORY': 'SUB_CATEGORY', 
        'SUB_CATEGORY': 'SUB_CATEGORY', 
        'SEASON': 'SEASON',
        'WARNA': 'WARNA',
        'UKURAN': 'UKURAN',
        'TAHUN PRODUKSI': 'TAHUN PRODUKSI', 
        'TAHUN LAUNCHING': 'TAHUN PRODUKSI',
        'TAHUN': 'TAHUN PRODUKSI', # Added mapping for 'TAHUN'
        'SINGKATAN DARI NAMA PRODUK': 'SINGKATAN_NAMA_PRODUK', 
        'NAMA PRODUK': 'SINGKATAN_NAMA_PRODUK',
        'DEFFECT': 'DEFFECT' # Added mapping for 'DEFFECT'
    }
    # Create a normalized map for lookup: remove all whitespace and convert to uppercase for keys
    jenis_normalization_map = {
        re.sub(r'\s+', '', k).upper(): v for k, v in jenis_normalization_map_raw.items()
    }

    if file_uploader is not None:
        try:
            # Read only the first sheet or default sheet
            df_sku_master = pd.read_excel(file_uploader)
            # Clean column names from extra spaces and newline characters
            df_sku_master.columns = [re.sub(r'\s+', ' ', col).strip() for col in df_sku_master.columns]

            required_cols = ['CODE', 'ARTI', 'JENIS']
            if not all(col in df_sku_master.columns for col in required_cols):
                st.error(f"File Master SKU harus memiliki kolom: {', '.join(required_cols)}") # Translated
                return {}

            for index, row in df_sku_master.iterrows():
                code = str(row.get('CODE', '')).strip().upper()
                arti = str(row.get('ARTI', '')).strip()
                jenis_raw_from_excel = str(row.get('JENIS', '')).strip().upper() # Get JENIS from the column

                # Normalize the raw jenis string from Excel for lookup: remove all whitespace
                jenis_normalized_for_lookup = re.sub(r'\s+', '', jenis_raw_from_excel)

                jenis_key = jenis_normalization_map.get(jenis_normalized_for_lookup, None)

                if code and jenis_key and jenis_key in sku_decoder:
                    # Store the 'arti' in the nested structure: sku_decoder[data_type][code] = arti
                    sku_decoder[jenis_key][code] = arti
                elif code and jenis_raw_from_excel and jenis_key is None:
                    st.warning(f"Jenis '{jenis_raw_from_excel}' untuk kode '{code}' tidak dikenali di Master SKU. Data ini mungkin tidak digunakan.") # Translated
            return sku_decoder
        except Exception as e_load_sku:
            st.error(f"Gagal memuat Data Master SKU. Pastikan format file benar dan memiliki kolom 'CODE', 'ARTI', 'JENIS'. Error: {e_load_sku}") # Translated
            return {}
    return {}

def enrich_dataframe_with_sku_info(df, sku_decoder):
    """
    Parses SKU string to extract category, year, season, etc. information
    using vectorized Pandas operations for efficiency.
    """
    if df.empty or 'SKU' not in df.columns:
        # Add default unknown columns if SKU column is missing or df is empty
        default_sku_info_cols = [
            "Category", "Sub Category", "Tahun Produksi", "Season",
            "Singkatan Nama Produk", "Warna Produk", "Size Produk", "Is Deffect"
        ]
        for col in default_sku_info_cols:
            if col not in df.columns:
                df[col] = "Unknown " + col.replace(" ", "") # e.g., "UnknownCategory"
            else:
                df[col] = df[col].fillna(f"Unknown {col.replace(' ', '')}")
        return df

    df_copy = df.copy()
    df_copy['SKU_UPPER'] = df_copy['SKU'].astype(str).str.upper().fillna('')

    # Create Series for faster mapping from sku_decoder
    category_map = pd.Series(sku_decoder.get("CATEGORY", {}))
    sub_category_map = pd.Series(sku_decoder.get("SUB_CATEGORY", {}))
    season_map = pd.Series(sku_decoder.get("SEASON", {}))
    warna_map = pd.Series(sku_decoder.get("WARNA", {}))
    ukuran_map = pd.Series(sku_decoder.get("UKURAN", {}))
    tahun_produksi_map = pd.Series(sku_decoder.get("TAHUN PRODUKSI", {}))
    deffect_map = pd.Series(sku_decoder.get("DEFFECT", {}))
    singkatan_nama_produk_map = pd.Series(sku_decoder.get("SINGKATAN_NAMA_PRODUK", {}))

    # Initialize new columns with default "Unknown" values if they don't exist
    # This prevents KeyError if the column is not created by the parsing logic for some SKUs
    for col in ["Category", "Sub Category", "Tahun Produksi", "Season",
                "Singkatan Nama Produk", "Warna Produk", "Size Produk", "Is Deffect"]:
        if col not in df_copy.columns:
            df_copy[col] = f"Unknown {col.replace(' ', '')}"
        else:
            df_copy[col] = df[col].fillna(f"Unknown {col.replace(' ', '')}")


    # 1. Size Produk: Take the last 2 digits of the SKU product
    df_copy['Size Produk'] = df_copy['SKU_UPPER'].str[-2:].map(ukuran_map).fillna("Unknown Ukuran")

    # 2. Category: Take the first 3 letters and numbers of the SKU product
    df_copy['Category'] = df_copy['SKU_UPPER'].str[:3].map(category_map).fillna("Unknown Category")

    # 3. Sub Category: Take the first 4 letters and numbers of the SKU product
    df_copy['Sub Category'] = df_copy['SKU_UPPER'].str[:4].map(sub_category_map).fillna("Unknown Sub Category")

    # Regex to extract other parts of the SKU
    # Pattern: [Prefix (optional)][Year/Deffect][Season][Separator][ProductAbbr]-[Color][Size (already handled)]
    # Example SKUs: ZOZA21BAS-MIA-TBW35, Z11822BAS LUNA-BWT03, 201A21BAS-CND-ORG02, 202D24BAS-HTR-BLK01
    # This regex is designed to capture:
    # Group 1: Year or Deffect Code (e.g., 21, D1)
    # Group 2: Season (e.g., BAS)
    # Group 3: Product Name Abbreviation (e.g., MIA, LUNA, CND, HTR)
    # Group 4: Color (e.g., TBW, BWT, ORG, BLK)
    # Group 5: Size (e.g., 35, 03) - captured for completeness, but `Size Produk` uses `str[-2:]`
    regex_pattern_full = r'(?:[A-Z0-9]+?)?([0-9]{2}|D[0-9])([A-Z]{3})[ -]([A-Z]+)-([A-Z]{3})([0-9]{2})$'
    
    # Use .str.extract to get all parts at once. It returns a DataFrame.
    extracted_parts = df_copy['SKU_UPPER'].str.extract(regex_pattern_full)

    # Assign extracted parts to temporary columns, handling potential NaNs from non-matching SKUs
    df_copy['temp_Year_Deffect_Code'] = extracted_parts[0].fillna('')
    df_copy['temp_Season_Code'] = extracted_parts[1].fillna('')
    df_copy['temp_Product_Name_Code'] = extracted_parts[2].fillna('')
    df_copy['temp_Color_Code'] = extracted_parts[3].fillna('')

    # Handle 'Is Deffect' logic
    df_copy['Is Deffect'] = df_copy['temp_Year_Deffect_Code'].str.startswith('D')

    # Apply year mapping, prioritizing mapped values, then deffect logic, then default
    # First, try to map from the 'TAHUN PRODUKSI' decoder
    mapped_years = df_copy['temp_Year_Deffect_Code'].map(tahun_produksi_map)
    
    # Update 'Tahun Produksi' with mapped values where available
    df_copy['Tahun Produksi'] = mapped_years.fillna(df_copy['Tahun Produksi'])

    # Specific logic for deffect years if not found in map (e.g., D1 -> 2021)
    # Only apply this if 'Is Deffect' is True AND 'Tahun Produksi' is still 'Unknown Tahun' (meaning it wasn't mapped)
    deffect_mask = df_copy['Is Deffect'] & (df_copy['Tahun Produksi'] == "Unknown Tahun")
    if deffect_mask.any():
        deffect_digit = df_copy.loc[deffect_mask, 'temp_Year_Deffect_Code'].str[1].apply(pd.to_numeric, errors='coerce')
        df_copy.loc[deffect_mask, 'Tahun Produksi'] = (2020 + deffect_digit).astype(str).fillna("Unknown Tahun")

    # Apply other mappings, prioritizing regex extracted parts if available
    df_copy['Season'] = df_copy['temp_Season_Code'].map(season_map).fillna(df_copy['Season'])
    df_copy['Singkatan Nama Produk'] = df_copy['temp_Product_Name_Code'].map(singkatan_nama_produk_map).fillna(df_copy['Singkatan Nama Produk'])
    df_copy['Warna Produk'] = df_copy['temp_Color_Code'].map(warna_map).fillna(df_copy['Warna Produk'])

    # Clean up temporary columns
    df_copy = df_copy.drop(columns=[col for col in df_copy.columns if col.startswith('temp_') or col == 'SKU_UPPER'], errors='ignore')

    return df_copy


@st.cache_data
def load_data(file_uploader, file_type, sku_decoder): # sku_decoder added as parameter
    """
    General function to load data from an uploaded Excel file and enrich with SKU info.
    """
    if file_uploader is not None:
        try:
            df = pd.read_excel(file_uploader)
            df.columns = [re.sub(r'\s+', ' ', col).strip() for col in df.columns]

            if file_type == "sales":
                # First, normalize column names to handle variations
                df.columns = [col.strip() for col in df.columns] # Strip whitespace from all columns

                # Define a mapping for common column names to standardized names
                column_mapping = {
                    'Toka Ziel Kids Officia Shop': 'Nama Toko',
                    'SK U': 'SKU',
                    'Salesmen': 'Salesman',
                    'Pelanggan': 'Customer ID', # Map 'Pelanggan' to 'Customer ID'
                    'No Transaksi': 'No Transaksi', # Direct match
                    'No. Transaksi': 'No Transaksi', # Common variation
                    'ID Transaksi': 'No Transaksi', # Another common variation
                    'Nomor Transaksi': 'No Transaksi', # Another common variation
                    'Order ID': 'No Transaksi', # English variation
                    'Transaction ID': 'No Transaksi' # English variation
                }
                
                # Apply renaming using a filtered mapping to only rename existing columns
                rename_dict = {k: v for k, v in column_mapping.items() if k in df.columns}
                df = df.rename(columns=rename_dict)

                # Ensure 'No Transaksi' exists after renaming. If not, create a dummy one.
                if 'No Transaksi' not in df.columns:
                    st.warning("Kolom 'No Transaksi' (atau variasi seperti 'No. Transaksi', 'ID Transaksi') tidak ditemukan di data penjualan. Jumlah pesanan akan dihitung berdasarkan baris unik.")
                    df['No Transaksi'] = df.index.astype(str) # Use row index as a dummy transaction ID, convert to string

                df['Tanggal'] = pd.to_datetime(df['Tanggal'], format='%d/%m/%Y %H:%M', errors='coerce')
                
                # Apply clean_financial_string function to financial columns
                for column_name in ['QTY', 'Harga', 'Sub Total', 'Nett Sales', 'HPP', 'Gross Profit']:
                    df[column_name] = df[column_name].apply(clean_financial_string)
                
                # Enrich with SKU info
                df = enrich_dataframe_with_sku_info(df, sku_decoder)

                return df
            elif file_type == "inbound":
                df = df.rename(columns={
                    'purchaseorder_no': 'No PO',
                    'supplier_name': 'Nama Supplier',
                    'Qty Dipesan': 'Qty Dipesan Unit',
                    'bill_no': 'No Bill',
                    'Catatan': 'Catatan',
                    'Pajak.1': 'Pajak Total',
                    'amount': 'Amount'
                })
                if 'Tanggal' not in df.columns:
                    raise KeyError("Kolom 'Tanggal' tidak ditemukan setelah pembersihan dan penamaan ulang di Data Inbound.") # Translated
                df['Tanggal'] = pd.to_datetime(df['Tanggal'], errors='coerce')
                
                # Apply clean_financial_string function to financial columns
                for column_name in ['Qty Dipesan Unit', 'Qty Diterima', 'Harga', 'Amount', 'Sub Total', 'Diskon', 'Pajak Total', 'Grand Total']:
                    df[column_name] = df[column_name].apply(clean_financial_string)
                
                # Enrich with SKU info
                df = enrich_dataframe_with_sku_info(df, sku_decoder)

                return df
            elif file_type == "stock":
                df = df.rename(columns={
                    'Nama': 'Nama Item',
                    'is_bundle': 'Is Bundle'
                })
                # Apply clean_financial_string function to financial columns
                for column_name in ['QTY', 'Dipesan', 'Tersedia', 'Harga Jual', 'HPP', 'Nilai Persediaan']:
                    df[column_name] = df[column_name].apply(clean_financial_string)
                
                # Enrich with SKU info
                df = enrich_dataframe_with_sku_info(df, sku_decoder)
                return df
        except Exception as e_load_data:
            st.error(f"Gagal memuat file {file_type}. Pastikan format file benar. Error: {e_load_data}") # Translated
            return pd.DataFrame()
    return pd.DataFrame()

# --- Function to Save and Load Data (Firestore) ---
# Define a maximum number of rows per chunk (heuristic, adjust based on your data's row size)
MAX_ROWS_PER_CHUNK = 500 # This is an estimate, adjust if your rows are very large/small

def save_data_for_admin(dataframes, sku_decoder_data, firestore_db):
    """Saves dataframes and sku_decoder to Firestore for the admin user, with chunking for large DataFrames."""
    if firestore_db is None:
        st.sidebar.error("Firestore tidak terinisialisasi. Tidak dapat menyimpan data.") # Translated
        return

    try:
        admin_doc_ref = firestore_db.collection("admin_data").document(ADMIN_USER_ID)

        for key, df in dataframes.items():
            df_main_doc_ref = admin_doc_ref.collection("dataframes").document(key)
            chunks_collection_ref = df_main_doc_ref.collection("chunks")

            # Delete all existing chunks for this DataFrame before saving new ones
            # This ensures cleanliness and avoids stale data from previous saves
            existing_chunks = chunks_collection_ref.stream()
            for chunk_doc in existing_chunks:
                chunk_doc.reference.delete()
            
            # Delete the main document if it exists (to clear old single-document data)
            if df_main_doc_ref.get().exists:
                df_main_doc_ref.delete()

            if df.empty:
                st.sidebar.info(f"Data {key} kosong, dokumen terkait dihapus dari Firestore jika ada.") # Translated
                continue # Move to the next DataFrame

            # Convert DataFrame to a list of dictionaries
            # Use .map instead of .applymap for future compatibility and better performance
            records_to_save = df.map(lambda x: x.isoformat() if isinstance(x, datetime) else x).to_dict(orient='records')
            num_records = len(records_to_save)
            num_chunks = (num_records + MAX_ROWS_PER_CHUNK - 1) // MAX_ROWS_PER_CHUNK # Ceiling division

            # Save metadata about chunking in the main document
            df_main_doc_ref.set({"chunked": True, "num_chunks": num_chunks, "num_records": num_records})

            # Save data in chunks
            for i in range(num_chunks):
                start_idx = i * MAX_ROWS_PER_CHUNK
                end_idx = min((i + 1) * MAX_ROWS_PER_CHUNK, num_records)
                chunk_data = records_to_save[start_idx:end_idx]
                chunks_collection_ref.document(f"chunk_{i}").set({"data": chunk_data})
            
            st.sidebar.success(f"Data {key} berhasil disimpan ke Firestore dalam {num_chunks} chunk!") # Translated

        # Save SKU decoder (this is usually small, no chunking needed)
        admin_doc_ref.collection("metadata").document("sku_decoder").set({"decoder": sku_decoder_data})
        st.sidebar.success(f"SKU Decoder berhasil disimpan ke Firestore!") # Translated

        # Update a timestamp to invalidate cache for other users
        admin_doc_ref.collection("metadata").document("last_update").set({"timestamp": firestore.SERVER_TIMESTAMP})
        st.sidebar.success("Timestamp pembaruan data berhasil dicatat.") # Translated

    except Exception as e_save_firestore:
        st.sidebar.error(f"Gagal menyimpan data ke Firestore. Error: {e_save_firestore}") # Translated

# Removed @st.cache_data from this function
def load_data_from_admin(firestore_db, last_update_timestamp_str): # Renamed parameter to reflect it's a string
    """Loads dataframes and sku_decoder from Firestore for the admin user, handling chunked DataFrames."""
    loaded_dataframes = {
        'df_sales_combined': pd.DataFrame(),
        'df_inbound_combined': pd.DataFrame(),
        'df_stock_combined': pd.DataFrame()
    }
    loaded_sku_decoder = {}

    if firestore_db is None: # Use the original db name here
        st.sidebar.error("Firestore tidak terinisialisasi. Tidak dapat memuat data.") # Translated
        return loaded_dataframes, loaded_sku_decoder

    try:
        admin_doc_ref = firestore_db.collection("admin_data").document(ADMIN_USER_ID) # Use the original db name here

        # Load DataFrames
        for key in loaded_dataframes.keys():
            df_main_doc_ref = admin_doc_ref.collection("dataframes").document(key)
            main_doc = df_main_doc_ref.get()

            if main_doc.exists and main_doc.to_dict().get("chunked"):
                # Load from chunks subcollection
                chunks_collection_ref = df_main_doc_ref.collection("chunks")
                chunk_docs = chunks_collection_ref.stream()
                
                all_records = []
                for chunk_doc in chunk_docs:
                    all_records.extend(chunk_doc.to_dict().get("data", []))
                
                if all_records:
                    df = pd.DataFrame.from_records(all_records)
                    
                    # Convert date strings back to datetime objects
                    if 'Tanggal' in df.columns:
                        df['Tanggal'] = pd.to_datetime(df['Tanggal'], errors='coerce')
                    
                    # Robustness check for 'No Transaksi'
                    if key == 'df_sales_combined' and 'No Transaksi' not in df.columns:
                        st.warning(f"Menambahkan kolom 'No Transaksi' ke {key} saat memuat dari admin karena tidak ditemukan.")
                        df['No Transaksi'] = df.index.astype(str)

                    loaded_dataframes[key] = df
                    st.sidebar.info(f"Data {key} berhasil dimuat dari {len(all_records)} record dalam {main_doc.to_dict().get('num_chunks', 0)} chunk.")
                else:
                    st.sidebar.info(f"Dokumen {key} ditemukan tetapi tidak ada chunk data di Firestore di subkoleksi 'chunks' untuk admin.") # Translated
            else:
                st.sidebar.info(f"Dokumen {key} tidak ditemukan atau tidak di-chunk di Firestore untuk admin. Mencoba memuat sebagai satu dokumen.") # Translated
                # Fallback for old single-document saves (less likely to be used now)
                doc = df_main_doc_ref.get()
                if doc.exists and "data" in doc.to_dict():
                    data_from_firestore = doc.to_dict()["data"]
                    df = pd.DataFrame.from_records(data_from_firestore)
                    if 'Tanggal' in df.columns:
                        df['Tanggal'] = pd.to_datetime(df['Tanggal'], errors='coerce')
                    if key == 'df_sales_combined' and 'No Transaksi' not in df.columns:
                        st.warning(f"Menambahkan kolom 'No Transaksi' ke {key} saat memuat dari admin karena tidak ditemukan.")
                        df['No Transaksi'] = df.index.astype(str)
                    loaded_dataframes[key] = df
                    st.sidebar.info(f"Data {key} berhasil dimuat sebagai satu dokumen.")
                else:
                    st.sidebar.info(f"Dokumen {key} tidak ditemukan di Firestore untuk admin.") # Translated

        # Load SKU decoder
        sku_decoder_doc_ref = admin_doc_ref.collection("metadata").document("sku_decoder")
        sku_decoder_doc = sku_decoder_doc_ref.get()
        if sku_decoder_doc.exists and "decoder" in sku_decoder_doc.to_dict():
            loaded_sku_decoder = sku_decoder_doc.to_dict()["decoder"]
        else:
            st.sidebar.info("Dokumen SKU Decoder tidak ditemukan di Firestore untuk admin.") # Translated

    except Exception as e_load_firestore:
        st.sidebar.error(f"Gagal memuat data dari Firestore. Error: {e_load_firestore}") # Translated

    return loaded_dataframes, loaded_sku_decoder

# --- Initialize session state variables at the top of the script ---
# This ensures they exist on every rerun, including full page refreshes
if 'current_user_id' not in st.session_state:
    st.session_state['current_user_id'] = None
if 'is_admin' not in st.session_state:
    st.session_state['is_admin'] = False
if 'df_sales_combined' not in st.session_state:
    st.session_state['df_sales_combined'] = pd.DataFrame()
if 'df_inbound_combined' not in st.session_state:
    st.session_state['df_inbound_combined'] = pd.DataFrame()
if 'df_stock_combined' not in st.session_state:
    st.session_state['df_stock_combined'] = pd.DataFrame()
if 'sku_decoder' not in st.session_state:
    st.session_state['sku_decoder'] = {}

# --- Sidebar for File Upload & Login ---
st.sidebar.header("Autentikasi & Unggah Data") # Translated

# Use a text_input that directly updates session state based on its value
user_id_input_widget = st.sidebar.text_input(
    "Masukkan ID Pengguna Anda:",
    value=st.session_state['current_user_id'] if st.session_state['current_user_id'] else "", # Pre-fill if already logged in
    key="user_id_input"
)

# Button to trigger login and data load
if st.sidebar.button("Login / Muat Data", key="login_button"):
    if user_id_input_widget:
        st.session_state['current_user_id'] = user_id_input_widget
        st.session_state['is_admin'] = (user_id_input_widget == ADMIN_USER_ID)
        st.sidebar.success(f"Berhasil masuk sebagai {user_id_input_widget}.")
        # Trigger a rerun to load data based on the new session state
        st.rerun()
    else:
        st.sidebar.warning("Mohon masukkan ID Pengguna.")

# --- Data Loading from Firestore (runs on every script rerun if user is logged in and data not loaded) ---
# This ensures data is loaded automatically after a refresh or initial access
if st.session_state['current_user_id'] and st.session_state['df_sales_combined'].empty:
    st.sidebar.info("Memuat data dari Firestore...") # Translated
    
    # Fetch last update timestamp from Firestore to use as cache invalidator
    last_update_doc_ref = db.collection("admin_data").document(ADMIN_USER_ID).collection("metadata").document("last_update")
    
    last_update_timestamp_str = None # Initialize as None
    try:
        last_update_doc = last_update_doc_ref.get()
        if last_update_doc.exists:
            raw_timestamp = last_update_doc.to_dict().get("timestamp")
            if raw_timestamp:
                # Convert firestore.Timestamp to ISO format string for caching
                last_update_timestamp_str = raw_timestamp.isoformat()
    except Exception as e:
        st.sidebar.warning(f"Gagal mengambil timestamp pembaruan terakhir: {e}. Melanjutkan tanpa timestamp.") # Translated

    # Load data from Firestore
    loaded_dfs, loaded_decoder = load_data_from_admin(db, last_update_timestamp_str) 
    st.session_state['df_sales_combined'] = loaded_dfs['df_sales_combined']
    st.session_state['df_inbound_combined'] = loaded_dfs['df_inbound_combined']
    st.session_state['df_stock_combined'] = loaded_dfs['df_stock_combined']
    st.session_state['sku_decoder'] = loaded_decoder
    # No st.rerun() here, as data is now loaded into session_state and dashboard will render

# Display file upload section only if user is logged in AND is admin
if st.session_state['current_user_id']: # Check if any user is logged in
    st.sidebar.markdown(f"---")
    st.sidebar.markdown(f"**Selamat datang, {st.session_state['current_user_id']}!**") # Translated

    if st.session_state.get('is_admin', False): # Only display uploader if admin
        st.sidebar.markdown("Unggah file Excel Anda di bawah ini.") # Translated
        
        # Place file uploaders here
        uploaded_sku_master_file = st.sidebar.file_uploader("1. Unggah Data Master SKU (Excel)", type=["xlsx", "xls"], key="sku_master_uploader") # Translated
        uploaded_sales_file = st.sidebar.file_uploader("2. Unggah Data Penjualan (Excel)", type=["xlsx", "xls"], key="sales_uploader") # Translated
        uploaded_inbound_file = st.sidebar.file_uploader("3. Unggah Data Inbound Barang (Excel)", type=["xlsx", "xls"], key="inbound_uploader") # Translated
        uploaded_stock_file = st.sidebar.file_uploader("4. Unggah Data Stok Barang (Excel)", type=["xlsx", "xls"], key="stock_uploader") # Translated

        # Initialize temporary DataFrames for newly uploaded data
        # These now refer to st.session_state directly as the source of truth
        temp_sku_decoder = st.session_state.get('sku_decoder', {}) 
        temp_df_sales = st.session_state.get('df_sales_combined', pd.DataFrame())
        temp_df_inbound = st.session_state.get('df_inbound_combined', pd.DataFrame())
        temp_df_stock = st.session_state.get('df_stock_combined', pd.DataFrame())

        # Process SKU Master file upload (without direct rerun)
        if uploaded_sku_master_file:
            with st.spinner("Memproses Data Master SKU..."): # Translated
                temp_sku_decoder = load_sku_master(uploaded_sku_master_file)
                if not temp_sku_decoder:
                    st.sidebar.error("Data Master SKU kosong atau gagal dimuat. Pastikan file benar.") # Translated
                else:
                    st.session_state['sku_decoder'] = temp_sku_decoder # Update session state immediately
                    st.sidebar.success("Data Master SKU berhasil diunggah ke memori.") # Translated

        # Process sales file upload (without direct rerun)
        if uploaded_sales_file:
            if temp_sku_decoder: # Ensure SKU decoder exists
                with st.spinner("Memproses Data Penjualan..."): # Translated
                    # Pass sku_decoder to load_data for SKU enrichment
                    df_sales_raw = load_data(uploaded_sales_file, "sales", temp_sku_decoder) 
                    if not df_sales_raw.empty:
                        # --- ADDED ROBUSTNESS CHECK FOR 'No Transaksi' HERE ---
                        if 'No Transaksi' not in df_sales_raw.columns:
                            st.warning("Menambahkan kolom 'No Transaksi' ke data penjualan karena tidak ditemukan setelah pemrosesan.")
                            df_sales_raw.loc[:, 'No Transaksi'] = df_sales_raw.index.astype(str) # Use .loc
                        # --- END ROBUSTNESS CHECK ---

                        st.session_state['df_sales_combined'] = df_sales_raw # Update session state immediately
                        st.sidebar.success("Data Penjualan berhasil diunggah ke memori.") # Translated
                    else:
                        st.sidebar.error("Gagal memuat Data Penjualan. Pastikan format file benar.") # Translated
            else:
                st.sidebar.warning("Unggah Data Master SKU terlebih dahulu untuk parsing SKU pada Data Penjualan.") # Translated

        # Process inbound file upload (without direct rerun)
        if uploaded_inbound_file:
            if temp_sku_decoder:
                with st.spinner("Memproses Data Inbound..."): # Translated
                    # Pass sku_decoder to load_data for SKU enrichment
                    df_inbound_raw = load_data(uploaded_inbound_file, "inbound", temp_sku_decoder)
                    if not df_inbound_raw.empty:
                        st.session_state['df_inbound_combined'] = df_inbound_raw # Update session state immediately
                        st.sidebar.success("Data Inbound berhasil diunggah ke memori.") # Translated
                    else:
                        st.sidebar.error("Gagal memuat Data Inbound. Pastikan format file benar.") # Translated
            else:
                st.sidebar.warning("Unggah Data Master SKU terlebih dahulu untuk parsing SKU pada Data Inbound.") # Translated

        # Process stock file upload (without direct rerun)
        if uploaded_stock_file:
            if temp_sku_decoder:
                with st.spinner("Memproses Data Stok..."): # Translated
                    # Pass sku_decoder to load_data for SKU enrichment
                    df_stock_raw = load_data(uploaded_stock_file, "stock", temp_sku_decoder)
                    if not df_stock_raw.empty:
                        st.session_state['df_stock_combined'] = df_stock_raw # Update session state immediately
                        st.sidebar.success("Data Stok berhasil diunggah ke memori.") # Translated
                    else:
                        st.sidebar.error("Gagal memuat Data Stok. Pastikan format file benar.") # Translated
            else:
                st.sidebar.warning("Unggah Data Master SKU terlebih dahulu untuk parsing SKU pada Data Stok.") # Translated

        # Button to save all uploaded data and update dashboard
        if st.sidebar.button("Simpan Data & Perbarui Dashboard", key="save_update_button"): # Translated
            with st.spinner("Menyimpan data dan memperbarui dashboard..."): # Translated
                current_dataframes = {
                    'df_sales_combined': st.session_state['df_sales_combined'],
                    'df_inbound_combined': st.session_state['df_inbound_combined'],
                    'df_stock_combined': st.session_state['df_stock_combined']
                }
                save_data_for_admin(current_dataframes, st.session_state['sku_decoder'], db)
                st.rerun() # Only rerun after all data is saved
    else:
        st.sidebar.info("Anda masuk sebagai Pengguna. Hanya admin yang dapat mengunggah data.") # Translated


# --- Helper function for KPI cards ---
def display_kpi_card(title, value, color, unit=""):
    """Displays a single KPI card with title, value, and color."""
    st.markdown(f"""
    <div style="background-color:#F0F2F6; padding: 15px; border-radius: 10px; text-align: center; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); margin: 10px;">
        <h3 style="color:#303030; margin-bottom: 5px;">{title}</h3>
        <p style="font-size: 2em; color:{color}; font-weight: bold;">{value}{unit}</p>
    </div>
    """, unsafe_allow_html=True)

# --- Helper function for plotting predictions ---
def plot_forecast_results(historical_data, forecast_values, prediction_type, model_name, forecast_horizon):
    """
    Plots historical and forecast data and displays forecast values.
    """
    y_label = 'Penjualan Bersih (Rp)' if prediction_type == "Penjualan Bersih" else 'Jumlah Terjual (Unit)'
    title_prefix = 'Penjualan Bersih' if prediction_type == "Penjualan Bersih" else 'Jumlah Terjual'

    plot_df_historical = historical_data.reset_index()
    plot_df_historical.columns = ['Bulan', 'Value']
    plot_df_historical['Tipe Data'] = 'Historis' # Translated

    forecast_df_plot = forecast_values.reset_index()
    forecast_df_plot.columns = ['Bulan', 'Value']
    forecast_df_plot['Tipe Data'] = 'Prediksi' # Translated

    plot_df_combined = pd.concat([plot_df_historical, forecast_df_plot])
    plot_df_combined['Bulan'] = plot_df_combined['Bulan'].dt.strftime('%Y-%m')

    color_map = {'Historis': 'blue'} # Default historical color

    # Assign prediction color based on model
    if model_name == "Rata-rata Bergerak": # Translated
        color_map['Prediksi'] = 'red'
    elif model_name == "ETS":
        color_map['Prediksi'] = 'green'
    elif model_name == "ARIMA":
        color_map['Prediksi'] = 'purple'
    elif model_name == "Prophet":
        color_map['Prediksi'] = 'orange'

    fig_prediction = px.line(plot_df_combined, x='Bulan', y='Value', color='Tipe Data',
                             title=f'Tren {title_prefix} Historis dan Prediksi ({model_name})', # Translated
                             labels={'Value': y_label, 'Bulan': 'Bulan'}, # Translated
                             markers=True,
                             template='plotly_white',
                             color_discrete_map=color_map)
    st.plotly_chart(fig_prediction, use_container_width=True)
    st.markdown(f"**Nilai Prediksi {title_prefix} untuk {forecast_horizon} bulan ke depan:**") # Translated
    st.dataframe(forecast_values.apply(lambda x: f"Rp {x:,.2f}" if prediction_type == "Penjualan Bersih" else f"{x:,.0f} unit")) # Translated


# --- Main Dashboard ---
st.title("Dashboard Analisis Data Bisnis") # Translated
st.markdown("Dashboard ini membantu Anda menganalisis data penjualan, inbound, dan stok untuk mendapatkan wawasan bisnis.") # Translated

# Display dashboard only if user is logged in and basic data is available
if st.session_state['current_user_id'] and \
   not st.session_state.get('df_sales_combined', pd.DataFrame()).empty and \
   not st.session_state.get('df_inbound_combined', pd.DataFrame()).empty and \
   not st.session_state.get('df_stock_combined', pd.DataFrame()).empty and \
   st.session_state.get('sku_decoder', {}):

    # --- Interactive Filters ---
    st.sidebar.markdown("---")
    st.sidebar.header("Filter Data") # Translated

    df_sales_filtered = st.session_state['df_sales_combined'].copy()
    df_stock_filtered = st.session_state['df_stock_combined'].copy()
    df_inbound_filtered = st.session_state['df_inbound_combined'].copy()

    # Sales Date Filter
    min_date = df_sales_filtered['Tanggal'].min().date() if not df_sales_filtered['Tanggal'].empty else pd.Timestamp.now().date()
    max_date = df_sales_filtered['Tanggal'].max().date() if not df_sales_filtered['Tanggal'].empty else pd.Timestamp.now().date()

    date_range = st.sidebar.date_input(
        "Pilih Rentang Tanggal Penjualan", # Translated
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    if len(date_range) == 2:
        start_date = pd.to_datetime(date_range[0])
        end_date = pd.to_datetime(date_range[1])
        df_sales_filtered = df_sales_filtered[(df_sales_filtered['Tanggal'] >= start_date) & (df_sales_filtered['Tanggal'] <= end_date)]

    # Product Category Filter
    all_categories = ['Semua Kategori'] + list(st.session_state['df_sales_combined']['Category'].unique()) # Translated
    selected_categories = st.sidebar.multiselect("Filter Berdasarkan Kategori", all_categories, default='Semua Kategori') # Translated

    if 'Semua Kategori' not in selected_categories: # Translated
        df_sales_filtered = df_sales_filtered[df_sales_filtered['Category'].isin(selected_categories)]
        df_stock_filtered = df_stock_filtered[df_stock_filtered['Category'].isin(selected_categories)]
        df_inbound_filtered = df_inbound_filtered[df_inbound_filtered['Category'].isin(selected_categories)]

    # Sales Location Filter (NEW)
    # Ensure 'Lokasi' column exists in df_sales_combined
    if 'Lokasi' in st.session_state['df_sales_combined'].columns:
        all_locations = ['Semua Lokasi'] + list(st.session_state['df_sales_combined']['Lokasi'].unique()) # Translated
        selected_locations = st.sidebar.multiselect("Filter Berdasarkan Lokasi Penjualan", all_locations, default='Semua Lokasi') # Translated

        if 'Semua Lokasi' not in selected_locations: # Translated
            df_sales_filtered = df_sales_filtered[df_sales_filtered['Lokasi'].isin(selected_locations)]
    else:
        st.sidebar.warning("Kolom 'Lokasi' tidak ditemukan di Data Penjualan. Filter lokasi tidak tersedia.") # Translated

    # NEW: Product Name Filter
    if 'Nama Barang' in st.session_state['df_sales_combined'].columns:
        all_product_names = ['Semua Produk'] + list(st.session_state['df_sales_combined']['Nama Barang'].unique()) # Translated
        selected_product_names = st.sidebar.multiselect("Filter Berdasarkan Nama Produk", all_product_names, default='Semua Produk') # Translated
        if 'Semua Produk' not in selected_product_names: # Translated
            df_sales_filtered = df_sales_filtered[df_sales_filtered['Nama Barang'].isin(selected_product_names)]
            # Also filter stock and inbound data by product name if applicable
            if 'Nama Item' in df_stock_filtered.columns:
                df_stock_filtered = df_stock_filtered[df_stock_filtered['Nama Item'].isin(selected_product_names)]
            if 'Nama Barang' in df_inbound_filtered.columns: # Assuming inbound also has 'Nama Barang' or similar
                df_inbound_filtered = df_inbound_filtered[df_inbound_filtered['Nama Barang'].isin(selected_product_names)]
    else:
        st.sidebar.warning("Kolom 'Nama Barang' tidak ditemukan di Data Penjualan. Filter nama produk tidak tersedia.") # Translated


    st.header("Key Performance Summary") # Changed back to English
    
    # Row 1 Metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        display_kpi_card("Total Sales", f"Rp {df_sales_filtered['Nett Sales'].sum():,.2f}", "#4CAF50")
    with col2:
        display_kpi_card("Total Gross Profit", f"Rp {df_sales_filtered['Gross Profit'].sum():,.2f}", "#2196F3")
    with col3:
        display_kpi_card("Total QTY Sold", f"{df_sales_filtered['QTY'].sum():,.0f}", "#FF9800", " unit")
    
    # Row 2 Metrics
    col4, col5, col6 = st.columns(3)

    with col4:
        total_inbound_qty = df_inbound_filtered['Qty Diterima'].sum()
        display_kpi_card("Total Inbound Goods", f"{total_inbound_qty:,.0f}", "#673AB7", " unit")
    with col5:
        total_stock_available = df_stock_filtered['Tersedia'].sum()
        display_kpi_card("Total Available Stock", f"{total_stock_available:,.0f}", "#00BCD4", " unit")
    with col6:
        avg_stock_qty = df_stock_filtered['Tersedia'].mean() if not df_stock_filtered.empty else 0
        inventory_turnover = (df_sales_filtered['QTY'].sum() / avg_stock_qty) if avg_stock_qty > 0 else 0
        display_kpi_card("Stock Turnover", f"{inventory_turnover:,.2f}", "#9C27B0", "x")


    st.markdown("---")

    st.header("Analisis Penjualan") # Translated

    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12, tab13, tab14, tab15, tab16 = st.tabs([ # Added tab16
        "Berdasarkan Kategori", "Berdasarkan Sub Kategori", "Berdasarkan Tahun Produksi", # Translated
        "Berdasarkan Musim", "Berdasarkan Warna", "Berdasarkan Ukuran", "Analisis Profitabilitas",
        "Analisis Produk Deffect", # Existing tab
        "Prediksi Penjualan", # Existing tab
        "Perbandingan Periode", # Existing tab
        "Analisis Pelanggan", # Existing tab
        "Analisis Pemasok", # Existing tab
        "Peringatan & Notifikasi", # Existing tab
        "Analisis Skenario 'Bagaimana Jika'", # Existing tab
        "Analisis Korelasi", # Existing tab
        "Analisis Tren Harga Produk" # New tab
    ])

    with tab1:
        st.subheader("Penjualan Berdasarkan Kategori Produk") # Translated
        sales_by_category = df_sales_filtered.groupby('Category')['Sub Total'].sum().sort_values(ascending=False).reset_index()
        fig_sales_category = px.bar(sales_by_category, x='Category', y='Sub Total',
                                     title='Total Penjualan per Kategori', # Translated
                                     labels={'Sub Total': 'Total Penjualan (Rp)'}, # Translated
                                     color='Category',
                                     template='plotly_white')
        st.plotly_chart(fig_sales_category, use_container_width=True)

        # Drill-down for Category to Sub Category
        if not sales_by_category.empty:
            selected_category_for_drilldown = st.selectbox(
                "Pilih Kategori untuk Analisis Lebih Lanjut (Drill-down ke Sub Kategori)", # Translated
                ['Pilih Kategori'] + list(sales_by_category['Category'].unique()),
                key="drilldown_category_select"
            )
            if selected_category_for_drilldown != 'Pilih Kategori': # Translated
                st.subheader(f"Penjualan Berdasarkan Sub Kategori dalam Kategori: {selected_category_for_drilldown}") # Translated
                df_sales_drilldown = df_sales_filtered[df_sales_filtered['Category'] == selected_category_for_drilldown]
                sales_by_subcategory_drilldown = df_sales_drilldown.groupby('Sub Category')['Sub Total'].sum().sort_values(ascending=False).reset_index()
                
                if not sales_by_subcategory_drilldown.empty:
                    fig_sales_subcategory_drilldown = px.bar(sales_by_subcategory_drilldown, x='Sub Category', y='Sub Total',
                                                               title=f'Penjualan per Sub Kategori di {selected_category_for_drilldown}', # Translated
                                                               labels={'Sub Total': 'Total Penjualan (Rp)'}, # Translated
                                                               color='Sub Category',
                                                               template='plotly_white')
                    st.plotly_chart(fig_sales_subcategory_drilldown, use_container_width=True)
                else:
                    st.info(f"Tidak ada data sub kategori untuk kategori '{selected_category_for_drilldown}' dalam filter saat ini.") # Translated


    with tab2:
        st.subheader("Penjualan Berdasarkan Sub Kategori Produk") # Translated
        sales_by_subcategory = df_sales_filtered.groupby('Sub Category')['Sub Total'].sum().sort_values(ascending=False).reset_index()
        fig_sales_subcategory = px.bar(sales_by_subcategory, x='Sub Category', y='Sub Total',
                                        title='Total Penjualan per Sub Kategori', # Translated
                                        labels={'Sub Total': 'Total Penjualan (Rp)'}, # Translated
                                        color='Sub Category',
                                        template='plotly_white')
        st.plotly_chart(fig_sales_subcategory, use_container_width=True)

    with tab3:
        st.subheader("Penjualan Berdasarkan Tahun Produksi") # Translated
        sales_by_year = df_sales_filtered.groupby('Tahun Produksi')['Sub Total'].sum().sort_values(ascending=False).reset_index()
        fig_sales_year = px.bar(sales_by_year, x='Tahun Produksi', y='Sub Total',
                                title='Total Penjualan per Tahun Produksi', # Translated
                                labels={'Sub Total': 'Total Penjualan (Rp)'}, # Translated
                                color='Tahun Produksi',
                                template='plotly_white')
        st.plotly_chart(fig_sales_year, use_container_width=True)

    with tab4:
        st.subheader("Penjualan Berdasarkan Musim") # Translated
        sales_by_season = df_sales_filtered.groupby('Season')['Sub Total'].sum().sort_values(ascending=False).reset_index()
        fig_sales_season = px.bar(sales_by_season, x='Season', y='Sub Total',
                                  title='Total Penjualan per Musim', # Translated
                                  labels={'Sub Total': 'Total Penjualan (Rp)'}, # Translated
                                  color='Season',
                                  template='plotly_white')
        st.plotly_chart(fig_sales_season, use_container_width=True)

    with tab5:
        st.subheader("Penjualan Berdasarkan Warna Produk") # Translated
        sales_by_color = df_sales_filtered.groupby('Warna Produk')['Sub Total'].sum().sort_values(ascending=False).reset_index()
        fig_sales_color = px.bar(sales_by_color, x='Warna Produk', y='Sub Total',
                                 title='Total Penjualan per Warna Produk', # Translated
                                 labels={'Sub Total': 'Total Penjualan (Rp)'}, # Translated
                                 color='Warna Produk',
                                 template='plotly_white')
        st.plotly_chart(fig_sales_color, use_container_width=True)

    with tab6:
        st.subheader("Penjualan Berdasarkan Ukuran Produk") # Translated
        sales_by_size = df_sales_filtered.groupby('Size Produk')['Sub Total'].sum().sort_values(ascending=False).reset_index()
        fig_sales_size = px.bar(sales_by_size, x='Size Produk', y='Sub Total',
                                title='Total Penjualan per Ukuran Produk', # Translated
                                labels={'Sub Total': 'Total Penjualan (Rp)'}, # Translated
                                color='Size Produk',
                                template='plotly_white')
        st.plotly_chart(fig_sales_size, use_container_width=True)

    with tab7:
        st.subheader("Analisis Profitabilitas Berdasarkan Kategori") # Translated
        profit_by_category = df_sales_filtered.groupby('Category')['Gross Profit'].sum().sort_values(ascending=False).reset_index()
        fig_profit_category = px.bar(profit_by_category, x='Category', y='Gross Profit',
                                     title='Total Laba Kotor per Kategori', # Translated
                                     labels={'Gross Profit': 'Laba Kotor (Rp)'}, # Translated
                                     color='Category',
                                     template='plotly_white')
        st.plotly_chart(fig_profit_category, use_container_width=True)

        st.subheader("Analisis Profitabilitas Berdasarkan Sub Kategori") # Translated
        profit_by_subcategory = df_sales_filtered.groupby('Sub Category')['Gross Profit'].sum().sort_values(ascending=False).reset_index()
        fig_profit_subcategory = px.bar(profit_by_subcategory, x='Sub Category', y='Gross Profit',
                                         title='Total Laba Kotor per Sub Kategori', # Translated
                                         labels={'Gross Profit': 'Laba Kotor (Rp)'}, # Translated
                                         color='Sub Category',
                                         template='plotly_white')
        st.plotly_chart(fig_profit_subcategory, use_container_width=True)

    with tab8: # New tab for defect product analysis
        st.subheader("Analisis Produk Deffect") # Translated
        
        df_deffect_sales = df_sales_filtered[df_sales_filtered['Is Deffect'] == True].copy() # Ensure it's a copy

        if not df_deffect_sales.empty:
            total_deffect_sales = df_deffect_sales['Nett Sales'].sum()
            display_kpi_card("Total Penjualan Produk Deffect", f"Rp {total_deffect_sales:,.2f}", "#E91E63")
            st.write("") # Add some space

            st.subheader("Tren Penjualan Produk Deffect Bulanan") # Translated
            df_deffect_sales.loc[:, 'Bulan'] = df_deffect_sales['Tanggal'].dt.to_period('M').astype(str) # Use .loc
            monthly_deffect_sales = df_deffect_sales.groupby('Bulan')['Nett Sales'].sum().reset_index()
            
            fig_deffect_sales_trend = px.line(monthly_deffect_sales, x='Bulan', y='Nett Sales',
                                             title='Tren Penjualan Bersih Produk Deffect Bulanan', # Translated
                                             labels={'Nett Sales': 'Penjualan Bersih (Rp)'}, # Translated
                                             markers=True,
                                             template='plotly_white',
                                             color_discrete_sequence=px.colors.qualitative.Set1)
            st.plotly_chart(fig_deffect_sales_trend, use_container_width=True)

            st.subheader("Produk Deffect Terlaris (Berdasarkan QTY)") # Translated
            top_deffect_products_qty = df_deffect_sales.groupby('Nama Barang')['QTY'].sum().sort_values(ascending=False).head(10).reset_index()
            if not top_deffect_products_qty.empty:
                fig_top_deffect_products_qty = px.bar(top_deffect_products_qty, x='Nama Barang', y='QTY',
                                                       title='10 Produk Deffect Terlaris (QTY)', # Translated
                                                       labels={'QTY': 'Jumlah Terjual (Unit)'}, # Translated
                                                       color='QTY',
                                                       template='plotly_white',
                                                       color_discrete_sequence=px.colors.qualitative.Pastel1)
                st.plotly_chart(fig_top_deffect_products_qty, use_container_width=True)
            else:
                st.info("Tidak ada produk deffect yang terjual dalam rentang filter yang dipilih.") # Translated

        else:
            st.info("Tidak ada data penjualan produk deffect dalam rentang filter yang dipilih.") # Translated

    with tab9: # New tab for Sales Prediction
        st.subheader("Prediksi Penjualan Sederhana") # Translated

        if not df_sales_filtered.empty:
            # Aggregate sales data by month for Nett Sales
            df_sales_filtered.loc[:, 'Bulan'] = df_sales_filtered['Tanggal'].dt.to_period('M').astype(str) # Use .loc
            monthly_sales_nett = df_sales_filtered.groupby('Bulan')['Nett Sales'].sum().reset_index()
            monthly_sales_nett['Bulan'] = pd.to_datetime(monthly_sales_nett['Bulan'])
            monthly_sales_nett = monthly_sales_nett.set_index('Bulan').sort_index()

            # Aggregate sales data by month for QTY
            monthly_sales_qty = df_sales_filtered.groupby('Bulan')['QTY'].sum().reset_index()
            monthly_sales_qty['Bulan'] = pd.to_datetime(monthly_sales_qty['Bulan'])
            monthly_sales_qty = monthly_sales_qty.set_index('Bulan').sort_index()

            st.markdown("Pilih parameter untuk prediksi:") # Translated
            
            prediction_type = st.selectbox(
                "Pilih Tipe Prediksi", # Translated
                ("Penjualan Bersih", "Jumlah Terjual (QTY)"), # Translated
                key="prediction_type_selector"
            )

            model_choice = st.selectbox(
                "Pilih Model Prediksi", # Translated
                ("Rata-rata Bergerak", "Exponential Smoothing (ETS)", "ARIMA", "Prophet"), # Translated
                key="model_choice_selector"
            )

            forecast_horizon = st.slider("Horizon Prediksi (bulan ke depan)", min_value=1, max_value=6, value=3) # Translated

            # Prepare data based on prediction type
            if prediction_type == "Penjualan Bersih": # Translated
                data_to_predict = monthly_sales_nett['Nett Sales']
            else: # Jumlah Terjual (QTY)
                data_to_predict = monthly_sales_qty['QTY']

            # Ensure data_to_predict is a Series with a DatetimeIndex
            if not isinstance(data_to_predict.index, pd.DatetimeIndex):
                st.error("Indeks data harus berupa DatetimeIndex untuk prediksi.")
                st.stop() # Changed return to st.stop()

            # --- Prediction Logic based on Model Choice ---
            forecast_values = pd.Series()

            if model_choice == "Rata-rata Bergerak": # Translated
                window_size = st.slider("Ukuran Jendela Rata-rata Bergerak (bulan)", min_value=1, max_value=len(data_to_predict)-1 if len(data_to_predict) > 1 else 1, value=min(3, len(data_to_predict)-1 if len(data_to_predict) > 1 else 1)) # Translated
                if window_size < 1:
                    st.warning("Ukuran jendela rata-rata bergerak harus minimal 1.")
                    st.stop() # Changed return to st.stop()
                
                moving_average = data_to_predict.rolling(window=window_size).mean()
                last_ma_value = moving_average.iloc[-1] if not moving_average.isnull().all() else 0
                
                last_date = data_to_predict.index.max()
                future_dates = pd.date_range(start=last_date + pd.DateOffset(months=1), periods=forecast_horizon, freq='MS')
                forecast_values = pd.Series([last_ma_value] * forecast_horizon, index=future_dates)
                plot_forecast_results(data_to_predict, forecast_values, prediction_type, "Rata-rata Bergerak", forecast_horizon)

            elif model_choice == "Exponential Smoothing (ETS)": # Translated
                if len(data_to_predict) < 2:
                    st.warning("Tidak cukup data untuk model Exponential Smoothing. Diperlukan minimal 2 titik data.") # Translated
                    st.stop() # Changed return to st.stop()

                try:
                    # Simple ETS model (additive trend, no seasonality for simplicity)
                    # You might need to adjust trend/seasonal components based on your data
                    from statsmodels.tsa.holtwinters import ExponentialSmoothing # Import inside to avoid global import issues if not installed
                    model = ExponentialSmoothing(data_to_predict, trend='add', seasonal=None, initialization_method="estimated").fit()
                    forecast = model.forecast(forecast_horizon)
                    forecast_values = forecast
                    plot_forecast_results(data_to_predict, forecast_values, prediction_type, "ETS", forecast_horizon)

                except Exception as e_ets:
                    st.error(f"Gagal menjalankan model ETS. Error: {e_ets}") # Translated
                    st.info("Pastikan data Anda memiliki variasi yang cukup untuk model ETS.") # Translated

            elif model_choice == "ARIMA":
                st.markdown("Pilih order ARIMA (p, d, q):") # Translated
                col_arima1, col_arima2, col_arima3 = st.columns(3)
                with col_arima1:
                    p_order = st.number_input("Order p (AR)", min_value=0, value=1)
                with col_arima2:
                    d_order = st.number_input("Order d (I)", min_value=0, value=1)
                with col_arima3:
                    q_order = st.number_input("Order q (MA)", min_value=0, value=1)

                if len(data_to_predict) < (p_order + d_order + q_order + 1):
                    st.warning("Tidak cukup data untuk order ARIMA yang dipilih. Coba kurangi order atau berikan lebih banyak data.") # Translated
                    st.stop() # Changed return to st.stop()

                try:
                    from statsmodels.tsa.arima.model import ARIMA # Import inside
                    model = ARIMA(data_to_predict, order=(p_order, d_order, q_order))
                    model_fit = model.fit()
                    forecast = model_fit.forecast(steps=forecast_horizon)
                    forecast_values = forecast
                    plot_forecast_results(data_to_predict, forecast_values, prediction_type, f"ARIMA {p_order},{d_order},{q_order}", forecast_horizon)

                except Exception as e_arima:
                    st.error(f"Gagal menjalankan model ARIMA. Error: {e_arima}") # Translated
                    st.info("Coba sesuaikan order ARIMA (p, d, q) atau pastikan data Anda cukup stasioner.") # Translated

            elif model_choice == "Prophet":
                if len(data_to_predict) < 2:
                    st.warning("Tidak cukup data untuk model Prophet. Diperlukan minimal 2 titik data.") # Translated
                    st.stop() # Changed return to st.stop()

                # Prophet requires a DataFrame with 'ds' and 'y' columns
                prophet_df = data_to_predict.reset_index()
                prophet_df.columns = ['ds', 'y']
                
                try:
                    from prophet import Prophet # Import inside
                    m = Prophet()
                    m.fit(prophet_df)
                    
                    future = m.make_future_dataframe(periods=forecast_horizon, freq='MS')
                    forecast = m.predict(future)
                    
                    forecast_values = forecast[['ds', 'yhat']].set_index('ds')['yhat'].iloc[-forecast_horizon:]
                    plot_forecast_results(data_to_predict, forecast_values, prediction_type, "Prophet", forecast_horizon)

                except Exception as e_prophet:
                    st.error(f"Gagal menjalankan model Prophet. Error: {e_prophet}") # Translated
                    st.info("Pastikan data Anda memiliki minimal 2 titik data dan tidak ada nilai yang hilang.") # Translated
        else:
            st.info("Tidak ada data penjualan yang tersedia untuk prediksi dalam rentang filter yang dipilih.") # Translated


    st.subheader("Penjualan Berdasarkan Saluran") # Translated
    sales_by_channel = df_sales_filtered.groupby('Channel')['Sub Total'].sum().sort_values(ascending=False).reset_index()
    fig_sales_channel = px.pie(sales_by_channel, names='Channel', values='Sub Total',
                               title='Proporsi Penjualan per Saluran', # Translated
                               template='plotly_white')
    st.plotly_chart(fig_sales_channel, use_container_width=True)

    st.subheader("10 Produk Terlaris (Berdasarkan QTY)") # Translated
    top_selling_products_qty = df_sales_filtered.groupby('Nama Barang')['QTY'].sum().sort_values(ascending=False).head(10).reset_index()
    fig_top_products_qty = px.bar(top_selling_products_qty, x='Nama Barang', y='QTY',
                                   title='10 Produk Terlaris (QTY)', # Translated
                                   labels={'QTY': 'Jumlah Terjual (Unit)'}, # Translated
                                   color='QTY',
                                   template='plotly_white')
    st.plotly_chart(fig_top_products_qty, use_container_width=True)

    st.subheader("Tren Penjualan Bulanan") # Translated
    df_sales_filtered.loc[:, 'Bulan'] = df_sales_filtered['Tanggal'].dt.to_period('M').astype(str) # Use .loc
    monthly_sales = df_sales_filtered.groupby('Bulan')['Nett Sales'].sum().reset_index()
    fig_monthly_sales = px.line(monthly_sales, x='Bulan', y='Nett Sales',
                                 title='Tren Penjualan Bersih Bulanan', # Translated
                                 labels={'Nett Sales': 'Penjualan Bersih (Rp)'}, # Translated
                                 markers=True,
                                 template='plotly_white')
    st.plotly_chart(fig_monthly_sales, use_container_width=True)

    with tab10: # New tab for Period Comparison
        st.subheader("Analisis Perbandingan Periode") # Translated

        if not df_sales_filtered.empty:
            comparison_metric = st.selectbox(
                "Pilih Metrik untuk Perbandingan", # Translated
                ("Penjualan Bersih", "Jumlah Terjual (QTY)", "Laba Kotor"), # Translated
                key="comparison_metric_select"
            )
            comparison_type = st.selectbox(
                "Pilih Tipe Perbandingan", # Translated
                ("Tahun-ke-Tahun (Year-over-Year)", "Bulan-ke-Bulan (Month-over-Month)"), # Translated
                key="comparison_type_select"
            )

            # Prepare data for comparison
            df_sales_for_comparison = df_sales_filtered.copy()
            df_sales_for_comparison.loc[:, 'Tahun'] = df_sales_for_comparison['Tanggal'].dt.year # Use .loc
            df_sales_for_comparison.loc[:, 'Bulan'] = df_sales_for_comparison['Tanggal'].dt.month # Use .loc

            # Define metric_col and y_label here to ensure they are always set
            if comparison_metric == "Penjualan Bersih": # Translated
                metric_col = 'Nett Sales'
                y_label = 'Penjualan Bersih (Rp)'
            elif comparison_metric == "Jumlah Terjual (QTY)": # Translated
                metric_col = 'QTY'
                y_label = 'Jumlah Terjual (Unit)'
            else: # Laba Kotor
                metric_col = 'Gross Profit'
                y_label = 'Laba Kotor (Rp)'

            if comparison_type == "Tahun-ke-Tahun (Year-over-Year)": # Translated
                # Aggregate by month across years
                comparison_data = df_sales_for_comparison.groupby(['Tahun', 'Bulan'])[metric_col].sum().unstack(level=0)
                comparison_data.index = pd.to_datetime(comparison_data.index.map(lambda x: f"2000-{x}-01")) # Dummy year for plotting
                comparison_data = comparison_data.sort_index()

                if not comparison_data.empty:
                    fig_yoy = px.line(comparison_data,
                                      title=f'Perbandingan {comparison_metric} Tahun-ke-Tahun', # Translated
                                      labels={'value': 'Jumlah', 'index': 'Bulan', 'Tahun': 'Tahun'}, # Translated
                                      markers=True,
                                      template='plotly_white')
                    fig_yoy.update_xaxes(tickformat="%b") # Display month names
                    st.plotly_chart(fig_yoy, use_container_width=True)
                    st.markdown(f"**Data Perbandingan {comparison_metric} Tahun-ke-Tahun:**") # Translated
                    st.dataframe(comparison_data.map(lambda x: f"Rp {x:,.2f}" if comparison_metric != "Jumlah Terjual (QTY)" else f"{x:,.0f} unit")) # Replaced applymap with map
                else:
                    st.info("Tidak cukup data untuk perbandingan Tahun-ke-Tahun.") # Translated

            elif comparison_type == "Bulan-ke-Bulan (Month-over-Month)": # Translated
                # Aggregate by month and year
                monthly_data = df_sales_for_comparison.groupby(['Tahun', 'Bulan'])[metric_col].sum().reset_index()
                monthly_data.loc[:, 'Periode'] = pd.to_datetime(monthly_data['Tahun'].astype(str) + '-' + monthly_data['Bulan'].astype(str)) # Use .loc
                monthly_data = monthly_data.sort_values('Periode')

                if not monthly_data.empty:
                    # Calculate MoM change
                    monthly_data.loc[:, 'Previous_Month_Value'] = monthly_data[metric_col].shift(1) # Use .loc
                    monthly_data.loc[:, 'MoM_Change'] = monthly_data[metric_col] - monthly_data['Previous_Month_Value'] # Use .loc
                    monthly_data.loc[:, 'MoM_Growth_Rate'] = (monthly_data['MoM_Change'] / monthly_data['Previous_Month_Value']) * 100 # Use .loc

                    fig_mom = px.line(monthly_data, x='Periode', y=metric_col,
                                      title=f'Tren {comparison_metric} Bulanan', # Translated
                                      labels={'Periode': 'Periode', 'y': y_label}, # Translated
                                      markers=True,
                                      template='plotly_white')
                    st.plotly_chart(fig_mom, use_container_width=True)

                    st.markdown(f"**Perubahan {comparison_metric} Bulan-ke-Bulan:**") # Translated
                    st.dataframe(monthly_data[['Periode', metric_col, 'MoM_Change', 'MoM_Growth_Rate']].style.format({
                        metric_col: (lambda x: f"Rp {x:,.2f}" if comparison_metric != "Jumlah Terjual (QTY)" else f"{x:,.0f} unit"), # Translated
                        'MoM_Change': (lambda x: f"Rp {x:,.2f}" if comparison_metric != "Jumlah Terjual (QTY)" else f"{x:,.0f} unit"), # Translated
                        'MoM_Growth_Rate': "{:,.2f}%"
                    }))
                else:
                    st.info("Tidak cukup data untuk perbandingan Bulan-ke-Bulan.") # Translated
        else:
            st.info("Tidak ada data penjualan yang tersedia untuk analisis perbandingan periode.") # Translated

    # --- Helper function for robust qcut ---
    def safe_qcut(series, q=5, ascending=True):
        """
        Applies pd.qcut safely, handling cases with fewer unique values than quantiles
        and ensuring correct label assignment.
        """
        # Ensure the series is numeric before attempting qcut or rank
        series = pd.to_numeric(series, errors='coerce').fillna(0) # Convert to numeric, fill NaN with 0

        if series.nunique() < q:
            # If not enough unique values for 'q' quantiles, use rank
            if ascending:
                ranked_series = series.rank(method='dense', ascending=True)
                max_rank = ranked_series.max()
                # Scale ranks to 1 to q, fill any potential NaN from rank with 0 before converting to int
                return ((ranked_series - 1) / (max_rank - 1) * (q - 1) + 1).fillna(0).astype(int) if max_rank > 1 else ranked_series.fillna(0).astype(int)
            else:
                ranked_series = series.rank(method='dense', ascending=False)
                max_rank = ranked_series.max()
                return ((ranked_series - 1) / (max_rank - 1) * (q - 1) + 1).fillna(0).astype(int) if max_rank > 1 else ranked_series.fillna(0).astype(int)
        else:
            # If enough unique values, use qcut to create bins, then map to 1-q scores
            cut_series = pd.qcut(series, q, duplicates='drop')

            # Get unique categories (bins) and sort them to ensure consistent scoring
            unique_categories = sorted(cut_series.cat.categories)
            
            # Create a mapping from category interval to score (1 to N, where N is number of unique bins)
            if ascending:
                score_mapping = {category: i + 1 for i, category in enumerate(unique_categories)}
            else:
                score_mapping = {category: len(unique_categories) - i for i, category in enumerate(unique_categories)}
            
            # Apply the mapping and fill any potential NaN from mapping with 0 before converting to int
            return cut_series.map(score_mapping).fillna(0).astype(int)


    with tab11: # New tab for Customer Analysis with RFM
        st.subheader("Analisis Pelanggan (RFM)") # Translated

        # Check for 'Channel' and 'Customer ID'
        if 'Channel' in df_sales_filtered.columns and 'Customer ID' in df_sales_filtered.columns: 
            all_channels = ['Semua Channel'] + list(df_sales_filtered['Channel'].unique()) # Translated
            selected_channel_for_customer_analysis = st.selectbox(
                "Filter Pelanggan Berdasarkan Channel", # Translated
                all_channels,
                key="customer_channel_filter" # Changed key to reflect 'channel'
            )

            df_customer_analysis = df_sales_filtered.copy()
            if selected_channel_for_customer_analysis != 'Semua Channel': # Translated
                df_customer_analysis = df_customer_analysis[df_customer_analysis['Channel'] == selected_channel_for_customer_analysis] # Filter by 'Channel'

            if not df_customer_analysis.empty:
                # Group by Customer ID to get customer-level metrics
                customer_summary = df_customer_analysis.groupby('Customer ID').agg(
                    Total_Sales=('Nett Sales', 'sum'),
                    Total_QTY=('QTY', 'sum'),
                    Number_of_Orders=('No Transaksi', 'nunique') # Assuming 'No Transaksi' is unique per order
                ).reset_index()

                st.subheader("Ringkasan Pelanggan") # Translated
                col_cust1, col_cust2, col_cust3 = st.columns(3)
                with col_cust1:
                    display_kpi_card("Total Pelanggan Unik", f"{customer_summary['Customer ID'].nunique():,.0f}", "#FF5722") # Translated
                with col_cust2:
                    display_kpi_card("Rata-rata Penjualan per Pelanggan", f"Rp {customer_summary['Total_Sales'].mean():,.2f}", "#607D8B") # Translated
                with col_cust3:
                    display_kpi_card("Rata-rata Pesanan per Pelanggan", f"{customer_summary['Number_of_Orders'].mean():,.2f}", "#795548") # Translated

                st.subheader("10 Pelanggan Teratas (Berdasarkan Penjualan)") # Translated
                top_10_customers_sales = customer_summary.sort_values(by='Total_Sales', ascending=False).head(10)
                st.dataframe(top_10_customers_sales.style.format({
                    'Total_Sales': "Rp {:,.2f}",
                    'Total_QTY': "{:,.0f} unit",
                    'Number_of_Orders': "{:,.0f}"
                }))

                st.subheader("Distribusi Penjualan per Pelanggan") # Translated
                fig_customer_sales_dist = px.histogram(customer_summary, x='Total_Sales', nbins=20,
                                                       title='Distribusi Total Penjualan per Pelanggan', # Translated
                                                       labels={'Total_Sales': 'Total Penjualan (Rp)', 'count': 'Jumlah Pelanggan'}, # Translated
                                                       template='plotly_white')
                st.plotly_chart(fig_customer_sales_dist, use_container_width=True)

                # --- RFM Analysis ---
                st.markdown("---")
                st.subheader("Analisis Segmentasi Pelanggan (RFM)") # Translated

                if not df_customer_analysis.empty and 'Tanggal' in df_customer_analysis.columns:
                    # Calculate Recency
                    # Use the latest date in the filtered data as the 'current_date' for recency calculation
                    current_date_for_rfm = df_customer_analysis['Tanggal'].max() + pd.Timedelta(days=1) # One day after the last transaction
                    
                    rfm_recency = df_customer_analysis.groupby('Customer ID')['Tanggal'].max().apply(
                        lambda x: (current_date_for_rfm - x).days
                    ).reset_index(name='Recency')

                    # Calculate Frequency
                    rfm_frequency = df_customer_analysis.groupby('Customer ID')['No Transaksi'].nunique().reset_index(name='Frequency')

                    # Calculate Monetary
                    rfm_monetary = df_customer_analysis.groupby('Customer ID')['Nett Sales'].sum().reset_index(name='Monetary')

                    # Merge RFM components
                    rfm_df = pd.merge(rfm_recency, rfm_frequency, on='Customer ID')
                    rfm_df = pd.merge(rfm_df, rfm_monetary, on='Customer ID')

                    # --- IMPORTANT: Ensure RFM columns are numeric and without NaNs before scoring and formatting ---
                    rfm_df['Recency'] = pd.to_numeric(rfm_df['Recency'], errors='coerce').fillna(0)
                    rfm_df['Frequency'] = pd.to_numeric(rfm_df['Frequency'], errors='coerce').fillna(0)
                    rfm_df['Monetary'] = pd.to_numeric(rfm_df['Monetary'], errors='coerce').fillna(0)
                    # --- END IMPORTANT FIX ---

                    # Assign RFM Scores using the safe_qcut function
                    rfm_df.loc[:, 'R_Score'] = safe_qcut(rfm_df['Recency'], q=5, ascending=False) # Lower recency is better
                    rfm_df.loc[:, 'F_Score'] = safe_qcut(rfm_df['Frequency'], q=5, ascending=True) # Higher frequency is better
                    rfm_df.loc[:, 'M_Score'] = safe_qcut(rfm_df['Monetary'], q=5, ascending=True) # Higher monetary is better

                    # Convert scores to integers for easier concatenation
                    rfm_df.loc[:, 'R_Score'] = rfm_df['R_Score'].astype(int)
                    rfm_df.loc[:, 'F_Score'] = rfm_df['F_Score'].astype(int)
                    rfm_df.loc[:, 'M_Score'] = rfm_df['M_Score'].astype(int)

                    # Create RFM Score string
                    rfm_df.loc[:, 'RFM_Score'] = rfm_df['R_Score'].astype(str) + rfm_df['F_Score'].astype(str) + rfm_df['M_Score'].astype(str)

                    # Define RFM Segments (simplified example)
                    # You can customize these segments based on your business logic
                    def rfm_segment(row):
                        if row['R_Score'] >= 4 and row['F_Score'] >= 4 and row['M_Score'] >= 4:
                            return 'Champions' # Translated
                        elif row['R_Score'] >= 2 and row['F_Score'] >= 3 and row['M_Score'] >= 3:
                            return 'Loyal Customers' # Translated
                        elif row['R_Score'] <= 2 and row['F_Score'] >= 3 and row['M_Score'] >= 3:
                            return 'At Risk' # Translated
                        elif row['R_Score'] >= 3 and row['F_Score'] <= 2 and row['M_Score'] <= 2:
                            return 'New Customers' # Translated
                        else:
                            return 'Others' # Translated

                    rfm_df.loc[:, 'Segment'] = rfm_df.apply(rfm_segment, axis=1) # Use .loc

                    st.write("**Ringkasan Segmentasi RFM:**") # Translated
                    segment_counts = rfm_df['Segment'].value_counts().reset_index()
                    segment_counts.columns = ['Segment', 'Jumlah Pelanggan'] # Translated
                    st.dataframe(segment_counts)

                    st.write("**Detail Pelanggan dengan Skor RFM:**") # Translated
                    st.dataframe(rfm_df.style.format({
                        'Recency': "{:,.0f} hari", # Translated
                        'Frequency': "{:,.0f} pesanan", # Translated
                        'Monetary': "Rp {:,.2f}"
                    }))

                    fig_rfm_segments = px.pie(segment_counts, names='Segment', values='Jumlah Pelanggan',
                                              title='Distribusi Segmentasi Pelanggan RFM', # Translated
                                              template='plotly_white')
                    st.plotly_chart(fig_rfm_segments, use_container_width=True)

                else:
                    st.info("Tidak ada data penjualan yang cukup untuk melakukan analisis RFM.") # Translated
            else:
                st.info("Tidak ada data pelanggan yang tersedia untuk analisis dalam filter yang dipilih.") # Translated
        else:
            st.warning("Kolom 'Channel' atau 'Customer ID' tidak ditemukan di Data Penjualan. Analisis pelanggan tidak tersedia.") # Translated


    st.markdown("---")

    st.header("Analisis Stok dan Barang Masuk") # Translated

    st.subheader("Ringkasan Stok Saat Ini") # Translated
    st.dataframe(df_stock_filtered[['Nama Item', 'Category', 'Sub Category', 'Lokasi', 'QTY', 'Tersedia', 'Harga Jual', 'HPP', 'Nilai Persediaan']])

    st.subheader("Perbandingan Stok Tersedia vs. Barang Diterima (Inbound)") # Translated
    inbound_by_sku = df_inbound_filtered.groupby('SKU')['Qty Diterima'].sum().reset_index(name='Total Qty Diterima')
    stock_available = df_stock_filtered.groupby('SKU')['Tersedia'].sum().reset_index(name='Total Tersedia')

    comparison_df = pd.merge(stock_available, inbound_by_sku, on='SKU', how='outer').fillna(0)
    comparison_df = pd.merge(comparison_df, df_stock_filtered[['SKU', 'Nama Item', 'Category']].drop_duplicates(), on='SKU', how='left')
    comparison_df['Nama Item'] = comparison_df['Nama Item'].fillna(comparison_df['SKU'])

    fig_stock_inbound_comp = px.bar(comparison_df.sort_values(by='Total Tersedia', ascending=False).head(20),
                                    x='Nama Item', y=['Total Tersedia', 'Total Qty Diterima'],
                                    title='Stok Tersedia vs. Jumlah Barang Diterima per SKU (Top 20)', # Translated
                                    labels={'value': 'Jumlah', 'variable': 'Tipe'}, # Translated
                                    barmode='group',
                                    template='plotly_white')
    st.plotly_chart(fig_stock_inbound_comp, use_container_width=True)

    st.subheader("Distribusi Stok Berdasarkan Lokasi") # Translated
    stock_by_location = df_stock_filtered.groupby('Lokasi')['QTY'].sum().sort_values(ascending=False).reset_index()
    fig_stock_location = px.pie(stock_by_location, names='Lokasi', values='QTY',
                                title='Distribusi Stok Berdasarkan Lokasi', # Translated
                                template='plotly_white')
    st.plotly_chart(fig_stock_location, use_container_width=True)

    # --- Minimum Stock Notification ---
    st.markdown("---")
    st.header("Notifikasi Stok Minimum (Top 20 Produk Terlaris)") # Translated

    if not df_stock_filtered.empty and not df_sales_filtered.empty:
        # Get top 20 selling products by QTY
        top_20_products_skus = df_sales_filtered.groupby('SKU')['QTY'].sum().nlargest(20).index.tolist()
        
        # Filter stock data for only these top 20 products
        df_stock_top_20 = df_stock_filtered[df_stock_filtered['SKU'].isin(top_20_products_skus)].copy() # Ensure it's a copy

        if not df_stock_top_20.empty:
            min_stock_threshold = st.number_input(
                "Tetapkan Ambang Batas Stok Minimum (Unit) untuk Top 20 Produk", # Translated
                min_value=0,
                value=50,
                step=10,
                key="min_stock_threshold_top_20"
            )

            products_below_min_stock_top_20 = df_stock_top_20[df_stock_top_20['Tersedia'] < min_stock_threshold]

            if not products_below_min_stock_top_20.empty:
                st.warning(f"⚠️ **{len(products_below_min_stock_top_20)} dari 20 produk terlaris berada di bawah ambang batas stok minimum ({min_stock_threshold} unit)!**") # Translated
                st.dataframe(products_below_min_stock_top_20[[
                    'Nama Item', 'SKU', 'Category', 'Lokasi', 'Tersedia', 'Dipesan'
                ]].sort_values(by='Tersedia'))
                st.info("Rekomendasi: Pertimbangkan untuk segera melakukan pemesanan ulang untuk produk-produk ini guna menghindari kehabisan stok dan potensi kehilangan penjualan.") # Translated
            else:
                st.success("✅ Semua 20 produk terlaris berada di atas ambang batas stok minimum yang ditetapkan.") # Translated
        else:
            st.info("Tidak ada data stok untuk 20 produk terlaris dalam rentang filter yang dipilih.") # Translated
    else:
        st.info("Tidak ada data penjualan atau stok yang tersedia untuk notifikasi stok minimum Top 20 Produk.") # Translated


    st.markdown("---")

    st.header("Analisis Gabungan dan Wawasan") # Translated

    st.subheader("Rekomendasi Berdasarkan Data") # Translated

    # Adjustable parameters for stock recommendations
    st.markdown("### Penyesuaian Parameter Rekomendasi Stok") # Translated
    col_rec1, col_rec2 = st.columns(2)
    with col_rec1:
        low_stock_threshold = st.number_input(
            "Ambang Batas Stok Rendah (Unit)", # Translated
            min_value=0, value=50, step=10, key="low_stock_rec_threshold"
        )
    with col_rec2:
        high_stock_threshold = st.number_input(
            "Ambang Batas Stok Berlebih (Unit)", # Translated
            min_value=0, value=100, step=10, key="high_stock_rec_threshold"
        )

    st.write("**Produk dengan Stok Rendah dan Penjualan Tinggi:**") # Translated
    avg_sales_qty = df_sales_filtered['QTY'].mean()
    sales_agg = df_sales_filtered.groupby('SKU')['QTY'].sum().reset_index(name='TotalQTYTerjual')
    stock_agg = df_stock_filtered.groupby('SKU')['Tersedia'].sum().reset_index(name='TotalTersedia')

    merged_performance = pd.merge(sales_agg, stock_agg, on='SKU', how='left').fillna(0)
    low_stock_high_sales = merged_performance[
        (merged_performance['TotalTersedia'] < low_stock_threshold) & # Using adjustable threshold
        (merged_performance['TotalQTYTerjual'] > avg_sales_qty)
    ].copy() # Ensure it's a copy
    if not low_stock_high_sales.empty:
        low_stock_high_sales = pd.merge(low_stock_high_sales, df_stock_filtered[['SKU', 'Nama Item', 'Category']].drop_duplicates(), on='SKU', how='left')
        st.dataframe(low_stock_high_sales[['Nama Item', 'Category', 'TotalQTYTerjual', 'TotalTersedia']])
        st.info("Rekomendasi: Pertimbangkan untuk melakukan pemesanan ulang segera untuk produk-produk ini guna menghindari kehabisan stok dan potensi kehilangan penjualan.") # Translated
    else:
        st.info("Tidak ada produk dengan stok rendah dan penjualan tinggi yang teridentifikasi saat ini.") # Translated

    st.write("**Produk dengan Stok Berlebih:**") # Translated
    high_stock_low_sales = merged_performance[
        (merged_performance['TotalTersedia'] > high_stock_threshold) & # Using adjustable threshold
        (merged_performance['TotalQTYTerjual'] < avg_sales_qty)
    ].copy() # Ensure it's a copy
    if not high_stock_low_sales.empty:
        high_stock_low_sales = pd.merge(high_stock_low_sales, df_stock_filtered[['SKU', 'Nama Item', 'Category']].drop_duplicates(), on='SKU', how='left')
        st.dataframe(high_stock_low_sales[['Nama Item', 'Category', 'TotalQTYTerjual', 'TotalTersedia']])
        st.info("Rekomendasi: Pertimbangkan strategi promosi, diskon, atau penjualan cepat untuk produk-produk ini guna mengurangi biaya penyimpanan dan membebaskan modal.") # Translated
    else:
        st.info("Tidak ada produk dengan stok berlebih yang teridentifikasi saat ini.") # Translated


    # --- New tab for Supplier Analysis ---
    with tab12:
        st.subheader("Analisis Kinerja Pemasok") # Translated

        if not df_inbound_filtered.empty:
            # Aggregate inbound data by supplier
            supplier_performance = df_inbound_filtered.groupby('Nama Supplier').agg(
                Total_Qty_Received=('Qty Diterima', 'sum'),
                Total_Amount_Spent=('Amount', 'sum'),
                Number_of_Bills=('No Bill', 'nunique')
            ).reset_index()

            st.write("**Ringkasan Kinerja Pemasok:**") # Translated
            st.dataframe(supplier_performance.style.format({
                'Total_Qty_Received': "{:,.0f} unit",
                'Total_Amount_Spent': "Rp {:,.2f}",
                'Number_of_Bills': "{:,.0f}"
            }))

            # Top Suppliers by Quantity Received
            st.subheader("Pemasok Teratas Berdasarkan Kuantitas Diterima") # Translated
            top_suppliers_qty = supplier_performance.sort_values(by='Total_Qty_Received', ascending=False).head(10)
            fig_top_suppliers_qty = px.bar(top_suppliers_qty, x='Nama Supplier', y='Total_Qty_Received',
                                            title='10 Pemasok Teratas (Kuantitas Diterima)', # Translated
                                            labels={'Total_Qty_Received': 'Total Kuantitas Diterima (Unit)'}, # Translated
                                            color='Nama Supplier',
                                            template='plotly_white')
            st.plotly_chart(fig_top_suppliers_qty, use_container_width=True)

            # Top Suppliers by Amount Spent
            st.subheader("Pemasok Teratas Berdasarkan Jumlah Belanja") # Translated
            top_suppliers_amount = supplier_performance.sort_values(by='Total_Amount_Spent', ascending=False).head(10)
            fig_top_suppliers_amount = px.bar(top_suppliers_amount, x='Nama Supplier', y='Total_Amount_Spent',
                                               title='10 Pemasok Teratas (Jumlah Belanja)', # Translated
                                               labels={'Total_Amount_Spent': 'Total Jumlah Belanja (Rp)'}, # Translated
                                               color='Nama Supplier',
                                               template='plotly_white')
            st.plotly_chart(fig_top_suppliers_amount, use_container_width=True)

        else:
            st.info("Tidak ada data inbound yang tersedia untuk analisis pemasok.") # Translated

    # --- New tab for Alerts and Notifications ---
    with tab13:
        st.subheader("Peringatan dan Notifikasi Otomatis") # Translated
        st.markdown("Atur ambang batas untuk metrik kinerja utama. Anda akan melihat peringatan di sini jika metrik berada di bawah ambang batas yang ditentukan.") # Translated

        if not df_sales_filtered.empty:
            current_nett_sales = df_sales_filtered['Nett Sales'].sum()
            current_gross_profit = df_sales_filtered['Gross Profit'].sum()
            current_profit_margin = (current_gross_profit / current_nett_sales) * 100 if current_nett_sales > 0 else 0

            st.markdown("### Atur Ambang Batas") # Translated
            col_alert1, col_alert2, col_alert3 = st.columns(3)

            with col_alert1:
                min_sales_threshold = st.number_input(
                    "Penjualan Bersih Minimum (Rp)", # Translated
                    min_value=0.0,
                    value=10000000.0, # Example default
                    step=1000000.0,
                    format="%.2f",
                    key="min_sales_threshold"
                )
            with col_alert2:
                min_profit_threshold = st.number_input(
                    "Laba Kotor Minimum (Rp)", # Translated
                    min_value=0.0,
                    value=2000000.0, # Example default
                    step=100000.0,
                    format="%.2f",
                    key="min_profit_threshold"
                )
            with col_alert3:
                min_profit_margin_threshold = st.number_input(
                    "Margin Laba Kotor Minimum (%)", # Translated
                    min_value=0.0,
                    max_value=100.0,
                    value=20.0, # Example default
                    step=1.0,
                    format="%.2f",
                    key="min_profit_margin_threshold"
                )
            
            st.markdown("---")
            st.markdown("### Status Metrik Saat Ini") # Translated
            
            # Display current metrics
            col_status1, col_status2, col_status3 = st.columns(3)
            with col_status1:
                display_kpi_card("Penjualan Bersih Saat Ini", f"Rp {current_nett_sales:,.2f}", "#4CAF50") # Translated
            with col_status2:
                display_kpi_card("Laba Kotor Saat Ini", f"Rp {current_gross_profit:,.2f}", "#2196F3") # Translated
            with col_status3:
                display_kpi_card("Margin Laba Kotor Saat Ini", f"{current_profit_margin:,.2f}%", "#FF9800") # Translated

            st.markdown("---")
            st.markdown("### Peringatan") # Translated

            # Check thresholds and display alerts
            if current_nett_sales < min_sales_threshold:
                st.error(f"🚨 Peringatan: Penjualan Bersih saat ini (Rp {current_nett_sales:,.2f}) berada di bawah ambang batas minimum yang ditetapkan (Rp {min_sales_threshold:,.2f}).") # Translated
            else:
                st.success(f"✅ Penjualan Bersih saat ini (Rp {current_nett_sales:,.2f}) memenuhi ambang batas.") # Translated
            
            if current_gross_profit < min_profit_threshold:
                st.error(f"🚨 Peringatan: Laba Kotor saat ini (Rp {current_gross_profit:,.2f}) berada di bawah ambang batas minimum yang ditetapkan (Rp {min_profit_threshold:,.2f}).") # Translated
            else:
                st.success(f"✅ Laba Kotor saat ini (Rp {current_gross_profit:,.2f}) memenuhi ambang batas.") # Translated

            if current_profit_margin < min_profit_margin_threshold:
                st.error(f"🚨 Peringatan: Margin Laba Kotor saat ini ({current_profit_margin:,.2f}%) berada di bawah ambang batas minimum yang ditetapkan ({min_profit_margin_threshold:,.2f}%).") # Translated
            else:
                st.success(f"✅ Margin Laba Kotor saat ini ({current_profit_margin:,.2f}%) memenuhi ambang batas.") # Translated

        else:
            st.info("Tidak ada data penjualan yang tersedia untuk mengatur peringatan.") # Translated

    with tab14: # New tab for What-If Analysis
        st.subheader("Analisis Skenario 'Bagaimana Jika'") # Translated
        st.markdown("Simulasikan dampak perubahan harga atau kuantitas terjual pada penjualan dan laba Anda.") # Translated

        scenario_scope = st.radio(
            "Terapkan skenario ke:", # Translated
            ("Semua Penjualan", "Kategori Tertentu", "Produk Tertentu"), # Translated
            key="whatif_scope"
        )

        df_whatif_base = df_sales_filtered.copy() # Start with the currently filtered data

        if scenario_scope == "Kategori Tertentu": # Translated
            all_categories_for_whatif = list(df_whatif_base['Category'].unique())
            if not all_categories_for_whatif:
                st.warning("Tidak ada kategori yang tersedia untuk simulasi. Unggah data penjualan terlebih dahulu.") # Translated
                st.stop()
            selected_category_for_whatif = st.selectbox(
                "Pilih Kategori:", # Translated
                all_categories_for_whatif,
                key="whatif_category_select"
            )
        elif scenario_scope == "Produk Tertentu": # Translated
            all_product_names_for_whatif = list(df_whatif_base['Nama Barang'].unique())
            if not all_product_names_for_whatif:
                st.warning("Tidak ada produk yang tersedia untuk simulasi. Unggah data penjualan terlebih dahulu.") # Translated
                st.stop()
            selected_product_for_whatif = st.selectbox(
                "Pilih Produk:", # Translated
                all_product_names_for_whatif,
                key="whatif_product_select"
            )
        
        if not df_whatif_base.empty:
            st.markdown("---")
            st.markdown("### Atur Perubahan Skenario") # Translated
            col_whatif_input1, col_whatif_input2 = st.columns(2)
            with col_whatif_input1:
                price_change_percent = st.slider(
                    "Perubahan Harga (%)", # Translated
                    min_value=-50, max_value=50, value=0, step=1,
                    key="whatif_price_change"
                )
            with col_whatif_input2:
                qty_change_percent = st.slider(
                    "Perubahan Kuantitas Terjual (%)", # Translated
                    min_value=-50, max_value=50, value=0, step=1,
                    key="whatif_qty_change"
                )

            # Calculate hypothetical values
            df_whatif_simulated = df_whatif_base.copy()

            # Calculate original HPP per unit for all rows first (handle division by zero)
            df_whatif_simulated.loc[:, 'Original_HPP_Per_Unit'] = df_whatif_simulated.apply( # Use .loc
                lambda row: row['HPP'] / row['QTY'] if row['QTY'] > 0 else 0, axis=1
            )

            # Identify rows to apply changes to
            target_rows_mask = pd.Series([True] * len(df_whatif_simulated), index=df_whatif_simulated.index) # Default to all
            if scenario_scope == "Kategori Tertentu":
                target_rows_mask = df_whatif_simulated['Category'] == selected_category_for_whatif
            elif scenario_scope == "Produk Tertentu":
                target_rows_mask = df_whatif_simulated['Nama Barang'] == selected_product_for_whatif

            # Apply price change
            df_whatif_simulated.loc[target_rows_mask, 'Hypothetical_Harga'] = \
                df_whatif_simulated.loc[target_rows_mask, 'Harga'] * (1 + price_change_percent / 100)
            # For non-target rows, keep original price
            df_whatif_simulated.loc[~target_rows_mask, 'Hypothetical_Harga'] = \
                df_whatif_simulated.loc[~target_rows_mask, 'Harga']
            
            # Apply quantity change
            df_whatif_simulated.loc[target_rows_mask, 'Hypothetical_QTY'] = \
                df_whatif_simulated.loc[target_rows_mask, 'QTY'] * (1 + qty_change_percent / 100)
            # For non-target rows, keep original QTY
            df_whatif_simulated.loc[~target_rows_mask, 'Hypothetical_QTY'] = \
                df_whatif_simulated.loc[~target_rows_mask, 'QTY']

            # Recalculate Sub Total, Nett Sales, HPP, Gross Profit based on hypothetical values
            df_whatif_simulated.loc[:, 'Hypothetical_Sub_Total'] = \
                df_whatif_simulated['Hypothetical_QTY'] * df_whatif_simulated['Hypothetical_Harga'] # Use .loc
            df_whatif_simulated.loc[:, 'Hypothetical_Nett_Sales'] = \
                df_whatif_simulated['Hypothetical_Sub_Total'] # Use .loc
            
            # Calculate hypothetical HPP using original HPP per unit and hypothetical QTY
            df_whatif_simulated.loc[target_rows_mask, 'Hypothetical_HPP'] = \
                df_whatif_simulated.loc[target_rows_mask, 'Hypothetical_QTY'] * \
                df_whatif_simulated.loc[target_rows_mask, 'Original_HPP_Per_Unit']
            # For non-target rows, keep original HPP
            df_whatif_simulated.loc[~target_rows_mask, 'Hypothetical_HPP'] = \
                df_whatif_simulated.loc[~target_rows_mask, 'HPP']
            
            df_whatif_simulated.loc[:, 'Hypothetical_Gross_Profit'] = \
                df_whatif_simulated['Hypothetical_Nett_Sales'] - df_whatif_simulated['Hypothetical_HPP'] # Use .loc

            # Summarize results
            original_total_sales = df_whatif_base['Nett Sales'].sum()
            hypothetical_total_sales = df_whatif_simulated['Hypothetical_Nett_Sales'].sum()
            original_gross_profit = df_whatif_base['Gross Profit'].sum()
            hypothetical_gross_profit = df_whatif_simulated['Hypothetical_Gross_Profit'].sum()

            st.markdown("---")
            st.markdown("### Hasil Skenario") # Translated
            col_whatif_res1, col_whatif_res2 = st.columns(2)
            with col_whatif_res1:
                display_kpi_card("Penjualan Bersih Asli", f"Rp {original_total_sales:,.2f}", "#4CAF50") # Translated
            with col_whatif_res2:
                display_kpi_card("Penjualan Bersih Hipotetis", f"Rp {hypothetical_total_sales:,.2f}", "#FF9800") # Translated

            # Comparison Chart
            comparison_data = pd.DataFrame({
                'Metrik': ['Penjualan Bersih', 'Laba Kotor'], # Translated
                'Asli': [original_total_sales, original_gross_profit], # Translated
                'Hipotetis': [hypothetical_total_sales, hypothetical_gross_profit] # Translated
            })
            comparison_data_melted = comparison_data.melt(id_vars='Metrik', var_name='Tipe Data', value_name='Nilai') # Translated

            fig_whatif_comparison = px.bar(comparison_data_melted, x='Metrik', y='Nilai', color='Tipe Data',
                                            barmode='group',
                                            title='Perbandingan Hasil Asli vs. Hipotetis', # Translated
                                            labels={'Nilai': 'Jumlah (Rp)', 'Metrik': 'Metrik', 'Tipe Data': 'Tipe Data'}, # Translated
                                            template='plotly_white')
            st.plotly_chart(fig_whatif_comparison, use_container_width=True)

            scenario_target_text = ""
            if scenario_scope == 'Kategori Tertentu':
                scenario_target_text = f"untuk kategori **{selected_category_for_whatif}**"
            elif scenario_scope == "Produk Tertentu":
                scenario_target_text = f"untuk produk **{selected_product_for_whatif}**"
            else:
                scenario_target_text = "untuk **semua penjualan**"

            st.markdown(f"""
            <div style="background-color:#E8F5E9; padding: 10px; border-radius: 5px; margin-top: 20px;">
                <p style="font-size: 1.1em; color:#2E7D32;">
                    **Wawasan Skenario:**
                    <br>
                    Dengan perubahan harga sebesar **{price_change_percent}%** dan perubahan kuantitas terjual sebesar **{qty_change_percent}%**
                    {scenario_target_text},
                    penjualan bersih diproyeksikan berubah dari **Rp {original_total_sales:,.2f}** menjadi **Rp {hypothetical_total_sales:,.2f}**,
                    dan laba kotor diproyeksikan berubah dari **Rp {original_gross_profit:,.2f}** menjadi **Rp {hypothetical_gross_profit:,.2f}**.
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Tidak ada data penjualan yang tersedia untuk melakukan analisis 'Bagaimana Jika' dalam filter yang dipilih atau untuk item yang dipilih.") # Translated

    with tab15: # New tab for Correlation Analysis
        st.subheader("Analisis Korelasi Penjualan vs. Laba Kotor") # Translated
        st.markdown("Pahami hubungan antara penjualan bersih dan laba kotor pada berbagai tingkat agregasi.") # Translated

        if not df_sales_filtered.empty:
            correlation_level = st.selectbox(
                "Pilih Tingkat Agregasi untuk Analisis Korelasi:", # Translated
                ("Per Transaksi", "Per Produk", "Per Kategori", "Per Sub Kategori"), # Translated
                key="correlation_level_select"
            )

            df_correlation = df_sales_filtered.copy()
            group_by_cols = []
            x_label = "Penjualan Bersih (Rp)" # Translated
            y_label = "Laba Kotor (Rp)" # Translated
            title_suffix = ""

            if correlation_level == "Per Transaksi": # Translated
                # Ensure 'No Transaksi' column exists before grouping
                if 'No Transaksi' not in df_correlation.columns:
                    st.warning("Kolom 'No Transaksi' tidak ditemukan di data penjualan. Analisis korelasi 'Per Transaksi' tidak dapat dilakukan.")
                    # Optionally, you can try to create it here if it's truly missing, but it should be handled in load_data
                    # df_correlation['No Transaksi'] = df_correlation.index.astype(str)
                    st.stop() # Stop execution for this tab if critical column is missing
                title_suffix = " per Transaksi" # Translated
            elif correlation_level == "Per Produk": # Translated
                group_by_cols = ['Nama Barang']
                title_suffix = " per Produk" # Translated
            elif correlation_level == "Per Kategori": # Translated
                group_by_cols = ['Category']
                title_suffix = " per Kategori" # Translated
            elif correlation_level == "Per Sub Kategori": # Translated
                group_by_cols = ['Sub Category']
                title_suffix = " per Sub Kategori" # Translated
            
            if group_by_cols:
                df_correlation_agg = df_correlation.groupby(group_by_cols).agg(
                    Total_Nett_Sales=('Nett Sales', 'sum'),
                    Total_Gross_Profit=('Gross Profit', 'sum')
                ).reset_index()
            else:
                # For 'Per Transaksi', we need to sum up Nett Sales and Gross Profit per transaction
                # Assuming 'No Transaksi' uniquely identifies a transaction
                df_correlation_agg = df_correlation.groupby('No Transaksi').agg(
                    Total_Nett_Sales=('Nett Sales', 'sum'),
                    Total_Gross_Profit=('Gross Profit', 'sum')
                ).reset_index()
            
            if not df_correlation_agg.empty:
                # Calculate Pearson correlation coefficient
                correlation_coefficient = df_correlation_agg['Total_Nett_Sales'].corr(df_correlation_agg['Total_Gross_Profit'])
                st.info(f"Koefisien Korelasi Pearson antara Penjualan Bersih dan Laba Kotor{title_suffix}: **{correlation_coefficient:,.2f}**") # Translated
                
                st.markdown("""
                <div style="background-color:#E0F7FA; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                    <p style="font-size: 0.9em; color:#006064;">
                        **Interpretasi Koefisien Korelasi:**
                        <ul>
                            <li>**1.0:** Korelasi positif sempurna (saat satu naik, yang lain naik secara proporsional).</li>
                            <li>**0.0:** Tidak ada korelasi linier.</li>
                            <li>**-1.0:** Korelasi negatif sempurna (saat satu naik, yang lain turun secara proporsional).</li>
                            <li>**0.7 - 1.0 (atau -0.7 - -1.0):** Korelasi Kuat.</li>
                            <li>**0.3 - 0.7 (atau -0.3 - -0.7):** Korelasi Sedang.</li>
                            <li>**0.0 - 0.3 (atau -0.0 - -0.3):** Korelasi Lemah.</li>
                        </ul>
                    </p>
                </div>
                """, unsafe_allow_html=True)

                fig_correlation = px.scatter(df_correlation_agg, 
                                             x='Total_Nett_Sales', 
                                             y='Total_Gross_Profit',
                                             title=f'Korelasi Penjualan Bersih vs. Laba Kotor{title_suffix}', # Translated
                                             labels={'Total_Nett_Sales': x_label, 'Total_Gross_Profit': y_label},
                                             hover_name=group_by_cols[0] if group_by_cols else 'No Transaksi', # Show item name on hover
                                             template='plotly_white')
                st.plotly_chart(fig_correlation, use_container_width=True)
            else:
                st.info(f"Tidak ada data yang cukup untuk analisis korelasi {correlation_level} dalam filter yang dipilih.") # Translated
        else:
            st.info("Tidak ada data penjualan yang tersedia untuk analisis korelasi.") # Translated

    with tab16: # New tab for Product Price Trend Analysis
        st.subheader("Analisis Tren Harga Produk") # Translated
        st.markdown("Lihat bagaimana harga produk berubah seiring waktu.") # Translated

        if not df_sales_filtered.empty and 'Nama Barang' in df_sales_filtered.columns and 'Harga' in df_sales_filtered.columns:
            all_products_for_price_trend = ['Pilih Produk'] + list(df_sales_filtered['Nama Barang'].unique()) # Translated
            selected_product_for_price_trend = st.selectbox(
                "Pilih Produk untuk Analisis Tren Harga:", # Translated
                all_products_for_price_trend,
                key="price_trend_product_select"
            )

            if selected_product_for_price_trend != 'Pilih Produk': # Translated
                df_product_price_trend = df_sales_filtered[df_sales_filtered['Nama Barang'] == selected_product_for_price_trend].copy()
                
                if not df_product_price_trend.empty:
                    # Aggregate by date to get average price per day for the product
                    # Use mean in case a product has multiple price entries on the same day (e.g., due to different discounts)
                    daily_avg_price = df_product_price_trend.groupby('Tanggal')['Harga'].mean().reset_index()
                    daily_avg_price = daily_avg_price.sort_values('Tanggal')

                    fig_price_trend = px.line(daily_avg_price, x='Tanggal', y='Harga',
                                              title=f'Tren Harga untuk {selected_product_for_price_trend}', # Translated
                                              labels={'Harga': 'Harga (Rp)', 'Tanggal': 'Tanggal'}, # Translated
                                              markers=True,
                                              template='plotly_white')
                    st.plotly_chart(fig_price_trend, use_container_width=True)

                    st.markdown(f"**Ringkasan Tren Harga untuk {selected_product_for_price_trend}:**") # Translated
                    col_price_summary1, col_price_summary2, col_price_summary3 = st.columns(3)
                    with col_price_summary1:
                        display_kpi_card("Harga Minimum", f"Rp {daily_avg_price['Harga'].min():,.2f}", "#4CAF50") # Translated
                    with col_price_summary2:
                        display_kpi_card("Harga Maksimum", f"Rp {daily_avg_price['Harga'].max():,.2f}", "#2196F3") # Translated
                    with col_price_summary3:
                        display_kpi_card("Harga Rata-rata", f"Rp {daily_avg_price['Harga'].mean():,.2f}", "#FF9800") # Translated
                    
                    st.write("**Data Harga Harian:**") # Translated
                    st.dataframe(daily_avg_price.style.format({'Harga': "Rp {:,.2f}"}))
                else:
                    st.info(f"Tidak ada data harga yang tersedia untuk produk '{selected_product_for_price_trend}' dalam filter saat ini.") # Translated
            else:
                st.info("Silakan pilih produk untuk melihat tren harganya.") # Translated
        else:
            st.info("Kolom 'Nama Barang' atau 'Harga' tidak ditemukan di Data Penjualan, atau data penjualan kosong. Analisis tren harga produk tidak tersedia.") # Translated

    st.markdown("---")
    st.subheader("Tabel Data Mentah (untuk Pemeriksaan Detail)") # Translated
    with st.expander("Lihat Data Penjualan Lengkap"): # Translated
        st.dataframe(df_sales_filtered)
    with st.expander("Lihat Data Inbound Barang Lengkap"): # Translated
        st.dataframe(df_inbound_filtered)
    with st.expander("Lihat Data Stok Barang Lengkap"): # Translated
        st.dataframe(df_stock_filtered)

    # --- Report Export Functionality ---
    st.markdown("---")
    st.header("Ekspor Laporan") # Translated
    st.write("Unduh data yang difilter di bawah ini:") # Translated

    col_export1, col_export2, col_export3 = st.columns(3)

    with col_export1:
        csv_sales = df_sales_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Unduh Data Penjualan (CSV)", # Translated
            data=csv_sales,
            file_name="data_penjualan_filtered.csv", # Translated
            mime="text/csv",
            key="download_sales_csv"
        )
        # Create an in-memory Excel file for download
        excel_sales_buffer = io.BytesIO()
        df_sales_filtered.to_excel(excel_sales_buffer, index=False, engine='openpyxl')
        excel_sales_buffer.seek(0) # Rewind the buffer to the beginning
        st.download_button(
            label="Unduh Data Penjualan (Excel)", # Translated
            data=excel_sales_buffer,
            file_name="data_penjualan_filtered.xlsx", # Translated
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_sales_excel"
        )

    with col_export2:
        csv_inbound = df_inbound_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Unduh Data Inbound (CSV)", # Translated
            data=csv_inbound,
            file_name="data_inbound_filtered.csv", # Translated
            mime="text/csv",
            key="download_inbound_csv"
        )
        # Create an in-memory Excel file for download
        excel_inbound_buffer = io.BytesIO()
        df_inbound_filtered.to_excel(excel_inbound_buffer, index=False, engine='openpyxl')
        excel_inbound_buffer.seek(0) # Rewind the buffer to the beginning
        st.download_button(
            label="Unduh Data Inbound (Excel)", # Translated
            data=excel_inbound_buffer,
            file_name="data_inbound_filtered.xlsx", # Translated
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_inbound_excel"
        )

    with col_export3:
        csv_stock = df_stock_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Unduh Data Stok (CSV)", # Translated
            data=csv_stock,
            file_name="data_stock_filtered.csv", # Translated
            mime="text/csv",
            key="download_stock_csv"
        )
        # Create an in-memory Excel file for download
        excel_stock_buffer = io.BytesIO()
        df_stock_filtered.to_excel(excel_stock_buffer, index=False, engine='openpyxl')
        excel_stock_buffer.seek(0) # Rewind the buffer to the beginning
        st.download_button(
            label="Unduh Data Stok (Excel)", # Translated
            data=excel_stock_buffer,
            file_name="data_stock_filtered.xlsx", # Translated
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_stock_excel"
        )

else:
    # Display login message if no user_id in session state
    if not st.session_state['current_user_id']:
        st.info("Silakan masukkan ID Pengguna Anda di sidebar dan klik 'Login / Muat Data' untuk memulai.") # Translated
    else:
        # Message for non-admin users who are logged in but have no data (e.g., Firestore is empty)
        st.info("Anda masuk sebagai pengguna. Dashboard akan menampilkan data yang terakhir diunggah oleh admin. Saat ini tidak ada data yang tersedia.") # Translated
        st.markdown("""
        **Petunjuk untuk Admin:** # Translated
        Jika Anda adalah admin, silakan login dengan ID admin Anda, lalu unggah semua file data (Master SKU, Penjualan, Inbound, dan Stok) melalui sidebar, dan klik "Simpan Data & Perbarui Dashboard". # Translated
        """)
