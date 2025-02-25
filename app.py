import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
from datetime import date as dt
import os
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px
import base64
import hashlib
import requests

st.set_page_config(layout="wide")



st.markdown("""
    <style>
        header {visibility: hidden;}      
    </style>
    """, unsafe_allow_html=True)

def check_password():
    def make_hash(password):
        return hashlib.sha256(str.encode(password)).hexdigest()
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    if st.session_state.password_correct:
        return True

    dir = Path(__file__).parent if '__file__' in globals() else Path.cwd()
    bg_path = dir / "images" / "BIBLIOGO.png"
    
    def get_base64_encoded_image(bg_path):
        with open(bg_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
        
    st.markdown(f"""
    <style>
                
        [data-testid="stAppViewContainer"] {{
            background-image: url("data:image/jpg;base64,{get_base64_encoded_image(str(bg_path))}");
            background-size: cover;
            background-repeat: no-repeat;
            background-position: center;
            align-items: center;
            justify-content: center;
        }}
    </style>    
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:

        st.markdown('')
        with st.form(key='login_form'):
            st.markdown(
                """
                <style>
                    @import url('https://fonts.googleapis.com/css2?family=Poppins&display=swap');
                    .stForm {
                        
                        color: rgb(0, 0, 0);
                        width: 700px;
                        height: 400px;
                        box-shadow: 0 0 10px rgba(10, 10, 10, 0.5);
                        
                        
                        display: block;
                        border-radius: 20px;

                    }
                    .login-title {
                        font-family: 'Poppins', sans-serif;
                        font-size: 28px;
                        color: black;
                        text-align: center;
                    }
                    .stFormSubmitButton>button {
                        background-color: #162938;
                        width: 100%;
                        height: 45px;
                        color: white;
                    }

                    .stFormSubmitButton>button:hover {
                        background-color: #FF3333;
                        border: none;
                        color: white;
                    }
                    .stTextInput input {
                        background-color: #16293825;
                        border-radius: 10px;
                        padding: 10px;
                    }
                        
                </style>
                <h1 class="login-title">Admin Login</h1>
                """, 
                unsafe_allow_html=True
            )
            username = st.text_input('Username', placeholder='Enter Username')
            password = st.text_input('Password', type='password', placeholder='Enter Password')

            login_button = st.form_submit_button(label='Sign in')
            
            if login_button:
                if username == "admin" and password == "sjalibrary":
                    st.session_state.password_correct = True
                    st.rerun()
                else:
                    st.error("Invalid username or password")
            st.markdown('')
           
    st.markdown(
        "<p style='text-align: center; color: rgba(255,255,255,0.5); position: fixed; bottom: 20px; width: 100%; left: 0;'>"
        "© 2025 Library Management System. All rights reserved.</p>",
        unsafe_allow_html=True
    )
    return False


if check_password():

    def set_background():
        current_dir = Path(__file__).parent if '__file__' in globals() else Path.cwd()
        image_path = current_dir / "images" / "BIBLIOGO.png"
        
        page_bg_img = f"""
        <style>
        [data-testid="stAppViewContainer"] {{
            background-image: url("data:image/png;base64,{get_base64_encoded_image(str(image_path))}");
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
            background-blend-mode: darken;
        }}

        </style>
        """
        st.markdown(page_bg_img, unsafe_allow_html=True)

    def get_base64_encoded_image(image_path):
        import base64
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        return encoded_string

    set_background()
    with open('style.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


    def update_book_status(df):
        def count_borrowers(patron_str):
            if pd.isna(patron_str) or patron_str == '':
                return 0
            return len([p for p in str(patron_str).split(',') if p.strip()])
        
        df['Borrowers_Count'] = df['Patron'].apply(count_borrowers)
        df['Status'] = df.apply(lambda row: 'Inactive' if row['Borrowers_Count'] >= row['Quantity'] else 'Active', axis=1)
        df.drop('Borrowers_Count', axis=1, inplace=True)
        return df
    

    def save_inventory_to_xlsx(data, file_path='Database.xlsx'):
        if os.path.exists(file_path):
            existing_data = pd.read_excel(file_path, dtype={'ISBN': str})
            existing_data['ISBN'] = existing_data['ISBN'].str.strip()
            
            matching_book = existing_data[existing_data['ISBN'] == data['ISBN'].strip()]
            
            if not matching_book.empty:
                book_idx = matching_book.index[0]
                existing_data.at[book_idx, 'Quantity'] += data['Quantity']
                updated_data = existing_data
            else:
                updated_data = pd.concat([existing_data, pd.DataFrame([data])], ignore_index=True)
        else:
            updated_data = pd.DataFrame([data])
        
        updated_data = update_book_status(updated_data)
        updated_data.to_excel(file_path, index=False)
        return updated_data


    def count_borrowed_books(patron_string):
        if pd.isna(patron_string) or patron_string == '':
            return 0
        return len([date for date in str(patron_string).split(',') if date.strip()])

    def create_scanner_input(key, placeholder="Scan or enter ISBN"):
        isbn = st.text_input("ISBN", key=key, placeholder=placeholder, help="Use barcode scanner or enter manually")
        return isbn
    
    def log_transaction(transaction_type, isbn, student_name, year_level, section):    
        transaction_file = 'Transaction.xlsx'
        if os.path.exists(transaction_file):
            transactions_df = pd.read_excel(transaction_file)
        else:
            transactions_df = pd.DataFrame(columns=[
                'Transaction ID', 
                'Transaction Type', 
                'ISBN', 
                'Book Title',
                'Author',
                'Patron Name', 
                'Year Level', 
                'Section', 
                'Transaction Date',
                'Status'
            ])

        isbn = str(isbn).strip()
        
        try:
            inventory_df = pd.read_excel('Database.xlsx', dtype={'ISBN': str})  

            inventory_df['ISBN'] = inventory_df['ISBN'].str.strip()
            
            matching_books = inventory_df[inventory_df['ISBN'] == isbn]
            
            if matching_books.empty:
                print(f"No book found with ISBN: {isbn}")
                book_title = "Not Found"
                book_author = "Not Found"
            else:
                book_details = matching_books.iloc[0]
                book_title = book_details['Book Title']
                book_author = book_details['Author']
                print(f"Found book: {book_title} by {book_author}")  
                
        except Exception as e:
            print(f"Error accessing inventory: {str(e)}")
            book_title = "Error"
            book_author = "Error"

        new_transaction = {
            'Transaction ID': len(transactions_df) + 1,
            'Transaction Type': transaction_type,
            'Transaction Date': dt.today().strftime('%Y-%m-%d %H:%M:%S'),
            'ISBN': isbn,
            'Book Title': book_title,
            'Author': book_author,
            'Patron Name': student_name,
            'Year Level': year_level,
            'Section': section,
            'Status': 'Successful'
        }
        
        transactions_df = pd.concat([transactions_df, pd.DataFrame([new_transaction])], ignore_index=True)
        transactions_df.to_excel(transaction_file, index=False)

    def get_transaction_history(isbn=None, student_name=None):

        if not os.path.exists('Transaction.xlsx'):
            return pd.DataFrame()     
        transactions_df = pd.read_excel('Transaction.xlsx')

        if isbn:
            transactions_df = transactions_df[transactions_df['ISBN'] == isbn]
        if student_name:
            transactions_df = transactions_df[transactions_df['Patron Name'] == student_name]
            
        return transactions_df
    
    def load_inventory():
        if os.path.exists('Database.xlsx'):
            return pd.read_excel('Database.xlsx', dtype={'ISBN': str})
        return None

    def save_inventory(df):
        df.to_excel('Database.xlsx', index=False)

    def edit_inventory_item(df, isbn, updates):
        try:
            if isbn in df['ISBN'].values:
                for column, value in updates.items():
                    if column in df.columns:
                        df.loc[df['ISBN'] == isbn, column] = value
                df = update_book_status(df)
                save_inventory(df)
                return df
            return None
        except Exception as e:
            print(f"Error updating inventory: {e}")
            return None

    def delete_inventory_item(df, isbn):

        if isbn in df['ISBN'].values:
            book_row = df[df['ISBN'] == isbn].iloc[0]
            if pd.notna(book_row['Patron']) and book_row['Patron'] != '':
                return None, "Cannot delete book that is currently borrowed"
            
            df = df[df['ISBN'] != isbn]
            save_inventory(df)
            return df, "Book deleted successfully"
        return None, "Book not found"
    class BookInventory:
      
        def __init__(self):
            self.api_base_url = "https://openlibrary.org/api/books"
            
        def fetch_book_details(self, isbn: str):
            """Fetch book details from Open Library API using ISBN"""
            try:
                params = {
                    "bibkeys": f"ISBN:{isbn}",
                    "format": "json",
                    "jscmd": "data"
                }
                response = requests.get(self.api_base_url, params=params)
                response.raise_for_status()
                data = response.json()
                book_key = f"ISBN:{isbn}"
                if book_key not in data:
                    return None
                book_info = data[book_key]
                
                # Simplified subject handling - only get first subject
                subjects = book_info.get("subjects", [])
                if subjects:
                    if isinstance(subjects, list):
                        first_subject = subjects[0]
                        if isinstance(first_subject, dict):
                            categories = first_subject.get("name", "N/A")
                        else:
                            categories = str(first_subject)
                    else:
                        categories = str(subjects)
                else:
                    categories = "N/A"
                    
                # Publisher handling
                publishers = book_info.get("publishers", [])
                if publishers:
                    publisher_names = []
                    for pub in publishers:
                        if isinstance(pub, dict) and "name" in pub:
                            publisher_names.append(pub["name"])
                        elif isinstance(pub, str):
                            publisher_names.append(pub)
                    publisher = ", ".join(publisher_names) if publisher_names else "N/A"
                else:
                    publisher = "N/A"
                    
                # Language handling
                languages = book_info.get("languages", [])
                if languages:
                    if isinstance(languages, list) and languages:
                        first_lang = languages[0]
                        if isinstance(first_lang, dict) and "key" in first_lang:
                            language = first_lang["key"].split("/")[-1].upper()
                        else:
                            language = str(first_lang).upper()
                    else:
                        language = str(languages).upper()
                else:
                    language = "N/A"
                    
               
                book_details = {
                    "isbn": isbn,
                    "title": book_info.get("title", "N/A"),
                    "authors": ", ".join([author.get("name", "N/A") for author in book_info.get("authors", [])]) or "N/A",
                    "publisher": publisher,
                    "published_date": book_info.get("publish_date", "N/A"),
                    "page_count": book_info.get("number_of_pages", 0) or 0,
                    "categories": categories, 
                    "language": language
                }
                return book_details
                
            except requests.RequestException as e:
                st.error(f"Error fetching book details: {str(e)}")
                return None
            except Exception as e:
                st.error(f"Unexpected error processing book details: {str(e)}")
                return None
    
         
       
    

    def dashboard():
        st.sidebar.image("images/logo.png")           
        with st.sidebar:
            selected = option_menu(
                menu_title=None, 
                options=['Home', 'Check Out', 'Check In', 'Record', 'Inventory'],
                icons=['house-fill', 'bookmark-check-fill', 'back', 'folder-fill', 'clipboard-data']
            )
        

        #-------------------------------------------------------- HOME ---------------------------------------------------------------------------

        def get_base64_image(image_path):
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode()

        if selected == 'Home':
            img_base64 = get_base64_image("images/bibo.png")


            st.markdown(
                f"""
                <style>
                    .container {{
                        display: flex;
                        flex-direction: column;
                        justify-content: flex-end; 
                        align-items: center;
                        height: 65vh; 
                        left: 5%;
                        position: relative;
                    }}
                    .bottom-center img {{
                        width: 1200px;
                        max-width: 80%;
                    }}

                </style>
                <div class="container">
                    <div class="bottom-center">
                        <img src="data:image/png;base64,{img_base64}">
                    </div>   
                </div>
                """,
                unsafe_allow_html=True
            )

            st.markdown(
                """
                <p style='text-align: center; color: rgba(255,255,255,0.5); position: fixed; bottom: 20px; width: 70%; left: 20%;'>
                    <span style="font-weight: bold; font-size: 24px;">Welcome to BiblioGo!</span><br>
                    BiblioGo is a Library Management System designed to make book monitoring and borrowing easier at Saint Joseph Academy. 
                    It helps students and librarians check out, check in, record, and track books efficiently.
                    Developed by Group 2 of STEM 12 - Quezon, BiblioGo improves library access and organization, 
                    making the system faster, smarter, and more convenient.<br>
                    Start exploring and enjoy a better library experience!
                </p>
                """,
                unsafe_allow_html=True
            )

        #-------------------------------------------------------- INVENTORY ----------------------------------------------------------------------#
        if selected == 'Inventory':
            tab = st.tabs(['Inventory','Edit Inventory', 'View Inventory', 'Download Inventory', 'Add Manually'])
            with tab[3]:
                st.subheader('Download Inventory')
             
                with st.expander('Download and Edit Items'):
                    df = load_inventory() 
                    st.data_editor(df, width=None, height=None, use_container_width=False, hide_index=None, column_order=None, column_config=None, num_rows="fixed", disabled=False, key=None, on_change=None, args=None, kwargs=None)
   
            with tab[1]:
                st.subheader('Edit Inventory')
                df = load_inventory()             
                if df is not None:
                    search_term = st.text_input('Search for book to edit (Title/ISBN/Author)', 
                                                key='edit_search',
                                                placeholder='Enter book title, ISBN, or author name')
                    
                    if search_term:
                        # Create a mask for searching by Book Title, ISBN, or Author
                        mask = (df['Book Title'].str.contains(search_term, case=False, na=False)) | \
                               (df['ISBN'].str.contains(search_term, case=False)) | \
                               (df['Author'].str.contains(search_term, case=False, na=False))
                        search_results = df[mask]
            
                        if not search_results.empty:
                            # Display search results in a dataframe
                            st.dataframe(search_results[['Book Title', 'Author', 'ISBN', 'Quantity', 'Type', 'Category', 'No Pages', 'Publishing Date', 'Publisher', 'Language']],
                                         use_container_width=True)
            
                            # Let the user select the index number
                            selected_index = st.selectbox(
                                'Select book to edit by index:',
                                options=range(len(search_results)),
                                format_func=lambda idx: f"{search_results.iloc[idx]['Book Title']} ({search_results.iloc[idx]['ISBN']})"
                            )
            
                            # Retrieve the selected book using the index
                            selected_book = search_results.iloc[selected_index]
            
                            # Create the edit and delete tabs
                            edit_tab, delete_tab = st.tabs(['Edit Book', 'Delete Book'])
            
                            with edit_tab:
                                with st.form(key='edit_form'):
                                    st.markdown(
                                        """
                                        <style>
                                            @import url('https://fonts.googleapis.com/css2?family=Poppins&display=swap');
                                            .edit-form-title {
                                                font-family: 'Poppins', sans-serif;
                                                font-size: 28px;
                                                color: #2a2a2a;
                                                text-align: center;
                                            }
                                        </style>
                                        <h1 class="edit-form-title">Edit Details</h1>
                                        <p style="text-align: center;">Fill out the form to edit an item in the inventory.</p>
                                        """, 
                                        unsafe_allow_html=True
                                    )
                                    new_title = st.text_input('Book Title', value=selected_book['Book Title'] if pd.notna(selected_book['Book Title']) else '')
                                    new_author = st.text_input('Author', value=selected_book['Author'] if pd.notna(selected_book['Author']) else '')
                                    new_category = st.text_input('Category', value=selected_book['Category'] if pd.notna(selected_book['Category']) else '')
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        new_publisher = st.text_input('Publisher', value=selected_book['Publisher'] if pd.notna(selected_book['Publisher']) else '')
                                        sub_col1, sub_col2 = st.columns(2)
                                        with sub_col1:
                                            new_quantity = st.number_input('Quantity', min_value=1, value=int(selected_book['Quantity']) if pd.notna(selected_book['Quantity']) else 1)
                                        with sub_col2:
                                            new_no_pages = st.number_input('Number of Pages', min_value=1, value=int(selected_book['No Pages']) if pd.notna(selected_book['No Pages']) else 1)
                                    with col2:
                                        type_options = ['Textbooks', 'Journal', 'Research Paper', 'Magazine', 'Brochure', 'Literature']
                                        type_index = type_options.index(selected_book['Type']) if selected_book['Type'] in type_options else 0
                                        new_type = st.selectbox('Type', options=type_options, index=type_index)
            
                                        sub_col1, sub_col2 = st.columns(2)
                                        with sub_col1:
                                            new_publishing_date = st.text_input('Publishing Date', value=selected_book['Publishing Date'] if pd.notna(selected_book['Publishing Date']) else '')
                                        with sub_col2:
                                            new_language = st.text_input('Language', value=selected_book['Language'] if pd.notna(selected_book['Language']) else '')
                                        
                                        update_button = st.form_submit_button('Update Book')
            
                                    if update_button:
                                        updates = {
                                            'Book Title': new_title,
                                            'Author': new_author,
                                            'Quantity': new_quantity,
                                            'Type': new_type,
                                            'Category': new_category,
                                            'No Pages': new_no_pages,
                                            'Publishing Date': new_publishing_date,
                                            'Publisher': new_publisher,
                                            'Language': new_language
                                        }
            
                                        # Use the selected book's ISBN for updating
                                        updated_df = edit_inventory_item(df, selected_book['ISBN'], updates)
                                        if updated_df is not None:
                                            st.success('Book updated successfully!')
                                        else:
                                            st.error('Failed to update book.')
            
                            with delete_tab:
                                st.markdown('### Delete Book')
                                st.write(f"Book Title: {selected_book['Book Title']}")
                                st.write(f"Author: {selected_book['Author']}")
                                st.write(f"ISBN: {selected_book['ISBN']}")
            
                                confirm_delete = st.checkbox('I confirm that I want to delete this book from the inventory')
            
                                if st.button('Delete Book', disabled=not confirm_delete):
                                    # Use the selected book's ISBN for deletion
                                    updated_df, message = delete_inventory_item(df, selected_book['ISBN'])
                                    if updated_df is not None:
                                        st.success(message)
                                        st.rerun()
                                    else:
                                        st.error(message)
                        else:
                            st.warning('No books found matching your search term.')
                else:
                    st.error('No inventory database found.')


                with tab[2]:
                    st.subheader('Inventory Record')
                    record_data = pd.read_excel('Database.xlsx')
                    sub_tab = st.tabs(['Active Books', 'Inactive Books'])
                    
                    with sub_tab[0]:
                        st.subheader('Active Books')

                        active_books = df[df['Status'] == 'Active']
                        
                        ft_col_list_active = ['Quantity', 'Book Title', 'Author', 'ISBN', 'Type','Category', 'Publishing Date', 'No Pages', 'Status']
                        column_widths_active = [1, 4, 4, 4, 2, 2, 2, 1, 2]  

                        active_books_table = go.Figure(
                            data=[go.Table(
                                columnwidth=column_widths_active,
                                hoverlabel=dict(align='auto'),
                                header=dict(
                                    values=[f"<b>{col}</b>" for col in ft_col_list_active],  
                                    font_color='white',
                                    font_size=12,
                                    align='left',
                                    height=18,
                                    fill_color='#ff7b00' 
                                ),
                                cells=dict(
                                    values=[active_books[col] for col in ft_col_list_active], 
                                    font_size=12,
                                    height=24,
                                    align='left',
                                    font_color='black'
                                )
                            )]
                        )
                        row_count = len(active_books)
                        min_height = 200 
                        max_height = 700

                        table_height = min(max_height, max(min_height, row_count * 30 + 80))

                        active_books_table.update_layout(
                            margin=dict(t=0, b=0, l=0, r=0),
                            height=table_height,
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)'
                        )

                        st.plotly_chart(active_books_table, use_container_width=True)

                    with sub_tab[1]:
                        st.subheader('Inactive Books')

                        inactive_books = df[df['Status'] == 'Inactive']
                        
                        ft_col_list_active = ['Quantity', 'Book Title', 'Author', 'ISBN', 'Type','Category', 'Publishing Date', 'No Pages', 'Status']
                        column_widths_active = [1, 4, 4, 4, 2, 2, 2, 1, 2]  

                        inactive_books_table = go.Figure(
                            data=[go.Table(
                                columnwidth=column_widths_active,
                                hoverlabel=dict(align='auto'),
                                header=dict(
                                    values=[f"<b>{col}</b>" for col in ft_col_list_active],  
                                    font_color='white',
                                    font_size=12,
                                    align='left',
                                    height=18,
                                    fill_color='#162938' 
                                ),
                                cells=dict(
                                    values=[inactive_books[col] for col in ft_col_list_active],  
                                    font_size=12,
                                    height=24,
                                    align='left',
                                    font_color='black'
                                )
                            )]
                        )

                        row_count = len(inactive_books)
                        table_height = min(max_height, max(min_height, row_count * 30 + 80))


                        inactive_books_table.update_layout(
                            margin=dict(t=0, b=0, l=0, r=0),
                            height=table_height,
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)'
                        )

                        st.plotly_chart(inactive_books_table, use_container_width=True)

            with tab[4]:
                with st.form(key='inventory_form'):
                    st.markdown(
                    """
                    <style>
                        @import url('https://fonts.googleapis.com/css2?family=Poppins&display=swap');
                        .inventory-form-title {
                            font-family: 'Poppins', sans-serif;
                            font-size: 28px;
                            color: #2a2a2a;
                            text-align: center;
                        }
                    </style>
                    <h1 class="inventory-form-title">Add Book to Inventory</h1>
                    <p style="text-align: center;">Fill out the form to add book.</p>
                    """, 
                    unsafe_allow_html=True
                )

                    isbn = create_scanner_input('inventory_isbn')
                    book_title = st.text_input('Book Title', value='', key='book_title', placeholder='Enter Book Title')
                    author = st.text_input('Author', value='', key='author', placeholder='Enter Author Name')
                    category = st.text_input('Category', value='', key='category', placeholder='Enter Category')
                        
                    col1, col2 = st.columns(2)    
                    with col1:
                        publisher = st.text_input('Publisher', value='', key='publisher', placeholder='Enter Publisher')   
                        sub_col1, sub_col2 = st.columns(2)  
                        with sub_col1:    
                            publishing_date = st.text_input('Publishing Date', value='', key='publishing_date', placeholder='Enter Publishing Year')
                        with sub_col2:
                            language = st.text_input('Language', value='', key='language', placeholder='Enter Language')
                        


                    with col2:
                        type = st.selectbox('Type', options=['Textbooks', 'Journal', 'Research Paper', 'Magazine', 'Brochure', 'Literature'])
                        
                        sub_col1, sub_col2 = st.columns(2)
                        with sub_col1:
                            quantity = st.number_input('Quantity', min_value=1, step=1, value=1)
                        with sub_col2:
                            no_pages = st.number_input('Number of Pages', min_value=1, step=1, value=1)

                        st.markdown('')
                        submit_button = st.form_submit_button(label='**Add Item**', icon='🗂️')
                        

                    if submit_button:
                        if not book_title or not author or not isbn or not publishing_date or not quantity or not no_pages or not type or not publisher or not category or not language :
                            st.warning('Please fill out all fields.')
                        else:
                            inventory_data = {
                                'Date': dt.today().strftime('%Y-%m-%d'),
                                'Book Title': book_title,
                                'Author': author,
                                'ISBN': isbn,
                                'Publisher': publisher,
                                'Type': type,
                                'Category': category,
                                'Language': language,
                                'Quantity': quantity,
                                'No Pages': no_pages,
                                'Patron': '',
                                'Check Out Dates': ''
                            }

                            updated_df = save_inventory_to_xlsx(inventory_data)
   
                            if len(updated_df[updated_df['ISBN'] == isbn.strip()]) > 0:
                                book_data = updated_df[updated_df['ISBN'] == isbn.strip()].iloc[0]
                                st.success(f'Updated quantity for existing book. New total: {book_data["Quantity"]}')
                            else:
                                st.success('New item has been added successfully!')

            

            
                   


            

            with tab[0]:
                st.title('')
                with st.form(key='automatic_form'):

                    if "inventory" not in st.session_state:
                        st.session_state.inventory = BookInventory()

                    st.markdown(
                        """
                        <style>
                            @import url('https://fonts.googleapis.com/css2?family=Poppins&display=swap');
                            .automatic-form-title {
                                font-family: 'Poppins', sans-serif;
                                font-size: 28px;
                                color: #2a2a2a;
                                text-align: center;
                            }
                        </style>
                        <h1 class="automatic-form-title">Add Book to Inventory</h1>
                        <p style="text-align: center;">Fill out the form to add book.</p>
                        """, 
                        unsafe_allow_html=True
                    )

                    isbn = create_scanner_input('auto_inventory_isbn', placeholder="Scan or enter ISBN")
                    book_type = st.selectbox('Type', options=['Textbooks', 'Journal', 'Research Paper', 'Magazine', 'Brochure', 'Literature'])
                    quantity = st.number_input('Quantity', min_value=1, step=1)

                    fetch_button = st.form_submit_button(label="Search Book Details")

                    if fetch_button:
                        if not isbn:
                            st.warning("Please enter an ISBN.")
                        else:
                            book_details = st.session_state.inventory.fetch_book_details(isbn)
                            if book_details:
                                st.success(f"Book found: **{book_details['title']}** by {book_details['authors']}")
                                
                                # Store fetched details in session state, including type
                                st.session_state.fetched_book = {
                                    "isbn": book_details["isbn"],
                                    "title": book_details["title"],
                                    "authors": book_details["authors"],
                                    "publisher": book_details["publisher"],
                                    "published_date": book_details["published_date"],
                                    "page_count": book_details["page_count"],
                                    "categories": book_details["categories"],
                                    "language": book_details["language"],
                                    "quantity": quantity,
                                    "type": book_type  # Added the type field
                                }
                            else:
                                st.error("Book details not found. Please enter manually.")
                                
                                if "fetched_book" in st.session_state:
                                    del st.session_state.fetched_book  

                # Confirm and save book details
                if "fetched_book" in st.session_state:
                    with st.form(key='confirm_book_form'):
                        st.subheader("Confirm Book Details")

                        book = st.session_state.fetched_book
                        st.text_input("Book Title", value=book["title"], disabled=True)
                        st.text_input("Author(s)", value=book["authors"], disabled=True)
                        st.text_input("Publisher", value=book["publisher"], disabled=True)
                        st.text_input("Published Date", value=book["published_date"], disabled=True)
                        st.text_input("Category", value=book["categories"], disabled=True)
                        st.text_input("Language", value=book["language"], disabled=True)
                        st.number_input("Number of Pages", value=int(book["page_count"]), disabled=True)
                       

                        confirm_button = st.form_submit_button("Add Book to Inventory")

                        if confirm_button:
                            inventory_data = {
                                'Date': dt.today().strftime('%Y-%m-%d'),
                                'Book Title': book["title"],
                                'Author': book["authors"],
                                'ISBN': book["isbn"],
                                'Publishing Date': book["published_date"][:4] if book["published_date"] else '',
                                'Publisher': book["publisher"],
                                'Language': book["language"],
                                'Type': book["type"],  # Ensure it's saved
                                'Category': book["categories"],
                                'Quantity': book["quantity"],
                                'No Pages': book["page_count"],
                                'Patron': '',
                                'Check Out Dates': ''
                            }

                            updated_df = save_inventory_to_xlsx(inventory_data)

                            st.success(f"Book **{book['title']}** Added Successfully!")
                            del st.session_state.fetched_book  
                            
                        cancel_button = st.form_submit_button("Cancel")
                        
                        if cancel_button:
                            # Reset the session state or clear specific form entries
                            if 'fetched_book' in st.session_state:
                                del st.session_state.fetched_book  # Clear the current book data if present
                        
                            # You can also reset other fields or variables that store form values
                            st.rerun()

            

                        
            #-------------------------------------------------------- CHECK OUT ----------------------------------------------------------------------
        if selected == 'Check Out':
            # Initialize session state for input fields
            if 'checkout_isbn' not in st.session_state:
                st.session_state.checkout_isbn = ''
            if 'student_name' not in st.session_state:
                st.session_state.student_name = ''
            if 'section' not in st.session_state:
                st.session_state.section = ''
            if 'year_level' not in st.session_state:
                st.session_state.year_level = None
            if 'checkout_date' not in st.session_state:
                st.session_state.checkout_date = dt.datetime.today().date()
                
            st.subheader('Search Book to Check Out')
            search_term = st.text_input('Search by Book Title or Author', value='', key='search_term', placeholder='Enter search term')
            if search_term:
                if os.path.exists('Database.xlsx'):
                    df = pd.read_excel('Database.xlsx')
                    
                    # Ensure that 'Book Title' and 'Author' are strings, handling NaN values
                    search_results = df[df.apply(
                        lambda row: (str(row['Book Title']).lower() if isinstance(row['Book Title'], str) else '').find(search_term.lower()) != -1 or 
                                    (str(row['Author']).lower() if isinstance(row['Author'], str) else '').find(search_term.lower()) != -1,
                        axis=1
                    )]
                    
                    if not search_results.empty:
                        st.dataframe(search_results[['Book Title', 'Author', 'ISBN', 'Quantity', 'Type', 'Category', 'No Pages', 'Publishing Date', 'Publisher', 'Language']],
                                         use_container_width=True)
                    else:
                        st.warning('No matching records found.')
                else:
                    st.warning('No inventory data found.')

            st.markdown("---")
            with st.form(key='check_out_form'):
                st.markdown(
                    """
                    <style>
                        @import url('https://fonts.googleapis.com/css2?family=Poppins&display=swap');
                        .check-out-form-title {
                            font-family: 'Poppins', sans-serif;
                            font-size: 28px;
                            color: #2a2a2a;
                            text-align: center;
                        }
                    </style>
                    <h1 class="check-out-form-title">Check Out Book</h1>
                    <p style="text-align: center;">Fill out the form to check out a book.</p>
                    """, 
                    unsafe_allow_html=True
                )

                isbn = create_scanner_input('checkout_isbn')
                student_name = st.text_input('Patron', value='', key='student_name', placeholder='Enter Name of Student')
                checkout_date = st.date_input('Check Out Date', value=dt.today().date())

                col1, col2 = st.columns(2)
                with col1:
                        yearLevel = st.selectbox('Year Level', options=['Grade 7', 'Grade 8', 'Grade 9', 'Grade 10', 'Grade 11', 'Grade 12'], index=None)     
                with col2:
                        section = st.text_input('Section', value='', key='section', placeholder='Enter Section')
                        submit_button = st.form_submit_button(label='Check Out Book')
                        st.markdown('')

                if submit_button:
                    if not isbn or not student_name or not yearLevel or not section:
                            st.warning('Please fill out all required fields.')
                    else:
                        if os.path.exists('Database.xlsx'):
                            df = pd.read_excel('Database.xlsx', dtype={'ISBN': str})
                            df['ISBN'] = df['ISBN'].str.strip()
                                
                            matching_books = df[df['ISBN'] == isbn.strip()]
                                
                            if len(matching_books) > 0:
                                book_idx = matching_books.index[0]
                                    
                                df = update_book_status(df)
                                if df.at[book_idx, 'Status'] == 'Inactive':
                                        st.error('This book is currently unavailable for checkout.')
                                        st.stop()
                                    
                                for col in ['Patron', 'Check Out Dates', 'Year Level', 'Section', 'Status']:
                                        if col not in df.columns:
                                            df[col] = ''


                                formatted_date = checkout_date.strftime('%Y-%m-%d')
                                    
                                current_patron = str(df.at[book_idx, 'Patron']) if pd.notna(df.at[book_idx, 'Patron']) else ''
                                current_dates = str(df.at[book_idx, 'Check Out Dates']) if pd.notna(df.at[book_idx, 'Check Out Dates']) else ''
                                current_year = str(df.at[book_idx, 'Year Level']) if pd.notna(df.at[book_idx, 'Year Level']) else ''
                                current_section = str(df.at[book_idx, 'Section']) if pd.notna(df.at[book_idx, 'Section']) else ''

                                due_date = checkout_date + pd.Timedelta(days=3)
                                formatted_due_date = due_date.strftime('%Y-%m-%d')
                                    
                                if current_patron == '':
                                        df.at[book_idx, 'Patron'] = student_name
                                        df.at[book_idx, 'Check Out Dates'] = formatted_date
                                        df.at[book_idx, 'Year Level'] = yearLevel
                                        df.at[book_idx, 'Section'] = section
                                        df.at[book_idx, 'Due'] = formatted_due_date
                                else:
                                        df.at[book_idx, 'Patron'] = f"{current_patron}, {student_name}"
                                        df.at[book_idx, 'Check Out Dates'] = f"{current_dates}, {formatted_date}"
                                        df.at[book_idx, 'Year Level'] = f"{current_year}, {yearLevel}"
                                        df.at[book_idx, 'Section'] = f"{current_section}, {section}"
                                        df.at[book_idx, 'Due'] = f"{df.at[book_idx, 'Due Date']}, {formatted_due_date}"
                                    
                                df = update_book_status(df)
                                df.to_excel('Database.xlsx', index=False)
                                st.success('Book has been checked out successfully.')
                                log_transaction('Check Out', isbn, student_name, yearLevel, section)

                                # Clear form fields after submission
                                st.session_state.checkout_isbn = ''
                                st.session_state.student_name = ''
                                st.session_state.section = ''
                                st.session_state.year_level = None
                                st.session_state.checkout_date = dt.datetime.today().date()
                                st.rerun()
            


                            else:
                                st.error('Book not found in inventory.')
                        else:
                            st.error('Inventory database not found.')


        #-------------------------------------------------------- CHECK IN ---------------------------------------------------------------------
        if selected == 'Check In':
            st.subheader('Search Book to Check In')
            search_term = st.text_input('Search by ISBN', value='', key='search_term', placeholder='Enter ISBN')
            
            if search_term:
                if os.path.exists('Database.xlsx'):
                    df = pd.read_excel('Database.xlsx')
                            
                    search_results = df[df.apply(
                            lambda row: search_term.lower() in str(row['ISBN']).lower(), axis=1
                        )]
                            
                    if not search_results.empty:
                            st.dataframe(search_results[['Book Title', 'Author', 'ISBN', 'Type', 'Category', 'Publishing Date', 'Publisher', 'Patron','Due']],
                                         use_container_width=True)
                        
                    else:
                        st.warning('No matching records found.')
                else:
                    st.warning('No inventory data found.')
            st.markdown("---")
            with st.form(key='check_in_form'):
                st.markdown(
                        """
                        <style>
                            @import url('https://fonts.googleapis.com/css2?family=Poppins&display=swap');
                            .check-in-form-title {
                                font-family: 'Poppins', sans-serif;
                                font-size: 28px;
                                color: #2a2a2a;
                                text-align: center;
                            }
                        </style>
                        <h1 class="check-in-form-title">Check In Book</h1>
                        <p style="text-align: center;">Fill out the form to return a book.</p>
                        """, 
                        unsafe_allow_html=True
                    )
                    
                isbn = create_scanner_input('checkin_isbn')
                date = st.date_input('Date', value=dt.today())
                date = date.strftime('%Y-%m-%d')
                col1, col2 = st.columns(2)
                with col1:
                        yearLevel = st.selectbox('Year Level', options=['Grade 7', 'Grade 8', 'Grade 9', 'Grade 10', 'Grade 11', 'Grade 12'], index=None)

                with col2:
                        section = st.text_input('Section', value='', key='section', placeholder='Enter Section')
                        submit_button = st.form_submit_button(label='Return Book')
                        st.markdown('')

                if submit_button:
                    if not isbn or not yearLevel or not section:
                            st.warning('Please fill out all required fields.')
                    else:
                        if os.path.exists('Database.xlsx'):
                            df = pd.read_excel('Database.xlsx', dtype={'ISBN': str})
                            df['ISBN'] = df['ISBN'].str.strip()
                                
                            matching_books = df[df['ISBN'] == isbn.strip()]
                                
                            if len(matching_books) > 0:
                                book_idx = matching_books.index[0]
                                    
                                patron_list = str(df.at[book_idx, 'Patron']) if pd.notna(df.at[book_idx, 'Patron']) else ''
                                checkout_list = str(df.at[book_idx, 'Check Out Dates']) if pd.notna(df.at[book_idx, 'Check Out Dates']) else ''
                                year_list = str(df.at[book_idx, 'Year Level']) if pd.notna(df.at[book_idx, 'Year Level']) else ''
                                section_list = str(df.at[book_idx, 'Section']) if pd.notna(df.at[book_idx, 'Section']) else ''
                                due_date_list = str(df.at[book_idx, 'Due']) if pd.notna(df.at[book_idx, 'Due']) else ''  
                                    
                                if patron_list:
                                    patrons = [p.strip() for p in patron_list.split(',')]
                                    checkouts = [d.strip() for d in checkout_list.split(',')]
                                    years = [y.strip() for y in year_list.split(',')] if year_list else []
                                    sections = [s.strip() for s in section_list.split(',')] if section_list else []
                                    due_dates = [d.strip() for d in due_date_list.split(',')] if due_date_list else [] 
                                        
                                    student_name = patrons.pop(0)  # Automatically select the first patron
                                    checkouts.pop(0)
                                    due_dates.pop(0)
                                    if years:
                                        years.pop(0)
                                    if sections:
                                        sections.pop(0)
                                    
                                    df.at[book_idx, 'Patron'] = ', '.join(patrons) if patrons else ''
                                    df.at[book_idx, 'Check Out Dates'] = ', '.join(checkouts) if checkouts else ''
                                    df.at[book_idx, 'Year Level'] = ', '.join(years) if years else ''
                                    df.at[book_idx, 'Section'] = ', '.join(sections) if sections else ''
                                    df.at[book_idx, 'Due'] = ', '.join(due_dates) if due_dates else ''
                                    
                                    # Update status after modifying data
                                    df = update_book_status(df)
                                    df.to_excel('Database.xlsx', index=False)
                                    st.success(f'Book has been checked in successfully for {student_name}.')
                                    log_transaction('Check In', isbn, student_name, yearLevel, section)
                                else:
                                    st.error('No patron found for this book.')
                            else:
                                st.error('Book not found in inventory.')
                        else:
                            st.error('Inventory database not found.')




        #-------------------------------------------------------- RECORD ------------------------------------------------------------------------

        if selected == 'Record':

            record_data = pd.read_excel('Database.xlsx')
            total_books = int(record_data['Quantity'].sum()) 
            borrow_books = int(record_data['Check Out Dates'].apply(count_borrowed_books).sum())  
            available_books = total_books - borrow_books

            df_book_categories = record_data[record_data['Category'].notnull()]
            book_categories = df_book_categories.groupby('Category')['Quantity'].sum()
            df_cat = book_categories.reset_index()


          
            col1, col2, col3 = st.columns(3)


            with col1:

                st.markdown(
                    f"""
                    <div style="background: linear-gradient(135deg, #ffffff 0%, #dcffff  100%);
                                width: 100%;
                                padding: 1rem; 
                                border-radius: 0.5rem; 
                                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); 
                                text-align: center;">
                        <h3 style="font-size: 2rem; color: #001f54; "><i class="fa fa-book" style="margin-right: 10px; font-size: 2rem; color: #001f54;"></i>Number of Books</h3>
                        <p style="font-size: 4rem; font-weight: bold;">{total_books}</p>
                        <p style="font-size: 1rem;">Total Number of Books in the Library</p>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
                                
            with col2:
                st.markdown(
                    f"""
                    <div style="background: linear-gradient(135deg, #ffffff 0%, #dcffff  100%);
                                width: 100%;
                                padding: 1rem; 
                                border-radius: 0.5rem; 
                                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); 
                                text-align: center;">
                        <h3 style="font-size: 2rem; color: #001f54;"><i class="fa fa-bookmark" style="margin-right: 10px; font-size: 2rem; color: #001f54;"></i>Out Books</h3>
                        <p style="font-size: 4rem; font-weight: bold;">{borrow_books}</p>
                        <p style="font-size: 1rem;">Total Borrowed Books in the Library</p>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )

            with col3:
                st.markdown(
                    f"""
                    <div style="background: linear-gradient(135deg, #ffffff 0%, #dcffff 100%);
                                width: 100%;
                                padding: 1rem; 
                                border-radius: 0.5rem; 
                                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); 
                                text-align: center;">
                        <h3 style="font-size: 2rem; color: #001f54;"><i class="fa fa-book-open" style="margin-right: 10px; font-size: 2rem; color: #001f54;"></i>Available Books</h3>
                        <p style="font-size: 4rem; font-weight: bold;">{available_books}</p>
                        <p style="font-size: 1rem;">Total Available Books in the Library</p>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
            st.markdown('')

            st.markdown('----')
            if not df_cat.empty:    
                fig = px.bar(df_cat, 
                                x='Category',  
                                y='Quantity',  
                                color='Category',  
                                template='seaborn'
                    )

                    
                fig.update_layout(
                        plot_bgcolor='rgba(230, 26, 26, 0)',  
                        paper_bgcolor='rgba(255, 255, 255, 0)', 
                        title='',
                        xaxis_title='',  
                        yaxis_title='', 
                        title_yanchor='bottom',
                        title_font=dict(
                            color='#162938',  
                            size=30
                        ),
                        xaxis=dict(
                            title=None,  
                            tickfont=dict(color='white')  
                        ),
                        yaxis=dict(
                            title='',
                            tickfont=dict(color='white')
                        )
                    )

                

                st.plotly_chart(fig, use_container_width=True)
                    
            else:
                st.warning('No data found.')
   
                    
                
            st.markdown('----')
            st.subheader('Find by Filter')
            
            tab = st.tabs(['Books', 'Transaction'])

            with tab[0]:

                inventory_data = pd.read_excel('Database.xlsx')

                col1, col2 = st.columns(2)
                with col1:
                

                    sub_col = st.columns(3)

                    with sub_col[0]:
                        selected_categories = st.multiselect(
                            'Filter by Category:',
                            inventory_data['Category'].unique().tolist()
                        )
                    with sub_col[2]:
                        selected_language = st.multiselect(
                            'Filter by Language:',
                            inventory_data['Language'].unique().tolist()
                        )
                    with sub_col[1]:
                        selected_type = st.multiselect(
                            'Filter by Type:',
                            inventory_data['Type'].unique().tolist()
                        )

                # Apply filters only if at least one is selected
                if selected_categories or selected_type or selected_language:
                    filtered_data = inventory_data.copy()

                    if selected_categories:
                        filtered_data = filtered_data[filtered_data['Category'].isin(selected_categories)]
                    if selected_language:
                        filtered_data = filtered_data[filtered_data['Language'].isin(selected_language)]
                    if selected_type:
                        filtered_data = filtered_data[filtered_data['Type'].isin(selected_type)]

                    st.dataframe(filtered_data, use_container_width=True)



            with tab[1]:
                # Load transaction and book data with ISBN as a string
                transaction_data = pd.read_excel('Transaction.xlsx', dtype={'ISBN': str})
                book_data = pd.read_excel('Database.xlsx', dtype={'ISBN': str})

                # Strip spaces and ensure ISBN remains consistent
                transaction_data['ISBN'] = transaction_data['ISBN'].astype(str).str.strip()
                book_data['ISBN'] = book_data['ISBN'].astype(str).str.strip()


                # Merge transaction data with book data to get "Due"
                merged_data = transaction_data.merge(book_data[['ISBN', 'Due']], on='ISBN', how='left')

        
                # Reorder columns
                merged_data = merged_data[
                    ['Transaction ID', 'Patron Name', 'Transaction Type', 'Due', 'Status', 
                     'ISBN', 'Book Title', 'Author', 'Year Level', 'Section']
                ]


                col1, col2 = st.columns(2)
                with col1:
                  
                    sub_col = st.columns(3)

                    with sub_col[0]:
                        selected_types = st.multiselect(
                            'Filter by Transaction Type:',
                            transaction_data['Transaction Type'].unique().tolist()
                        )
                    with sub_col[1]:
                        selected_year_level = st.multiselect(
                            'Filter by Year Level:',
                            transaction_data['Year Level'].unique().tolist()
                        )
                    with sub_col[2]:
                        selected_section = st.multiselect(
                            'Filter by Section:',
                            transaction_data['Section'].unique().tolist()
                        )

                # Apply filters only if at least one filter is selected
                if selected_types or selected_year_level or selected_section:
                    filtered_data = merged_data.copy()

                    if selected_types:
                        filtered_data = filtered_data[filtered_data['Transaction Type'].isin(selected_types)]
                    if selected_year_level:
                        filtered_data = filtered_data[filtered_data['Year Level'].isin(selected_year_level)]
                    if selected_section:
                        filtered_data = filtered_data[filtered_data['Section'].isin(selected_section)]

                    st.dataframe(filtered_data, use_container_width=True)



    def main():
        dashboard()

    if __name__ == '__main__':
        main()

