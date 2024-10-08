import docx
import streamlit as st
import nltk
import spacy
from pytube import YouTube
nltk.download('stopwords')
spacy.load('en_core_web_sm')
from App import skill_mapping
import re
import docx2txt
import pandas as pd
import base64
import time,datetime
import random
from streamlit_tags import st_tags
from PIL import Image
import pymysql
from Courses import ds_course,web_course,android_course,ios_course,uiux_course,resume_videos,interview_videos




def display_docx_content(file_path):
    st.sidebar.info("Uploading your Resume....")

    st.subheader("Uploaded Resume:")
    st.text(file_path)
    st.success("Resume uploaded successfully!")

    # Read the content of the DOCX file
    resume_text = docx2txt.process(file_path)

    st.subheader("Resume Content:")

    # Display resume text without overflowing the box
    with st.expander("Click to see full resume"):
        st.code(resume_text, language='text')

    st.markdown("---")

    st.subheader("Resume Analysis:")
    st.text("Performing analysis on your resume...")

    # Perform analysis or other operations as needed

    st.balloons()


def fetch_yt_video(link):
    try:
        youtube = YouTube(link)
        video_title = youtube.title
        return video_title if video_title else "Unknown Title"
    except Exception as e:
        st.error(f"Error fetching YouTube video: {e}")
        return "Unknown Title"



def get_table_download_link(df,filename,text):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    # some strings <-> bytes conversions necessary here
    # href = f'<a href="data:file/csv;base64,{b64}">Download Report</a>'
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href





def course_recommender(course_list):
    st.subheader("**Courses & Certificates🎓 Recommendations**")
    c = 0
    rec_course = []
    no_of_reco = st.slider('Choose Number of Course Recommendations:', 1, 10, 4)
    random.shuffle(course_list)
    for c_name, c_link in course_list:
        c += 1
        st.markdown(f"({c}) [{c_name}]({c_link})")
        rec_course.append(c_name)
        if c == no_of_reco:
            break
    return rec_course


connection = pymysql.connect(host='localhost', user='root', password='')
cursor = connection.cursor()




def insert_data(name, email, res_score, timestamp, no_of_pages, reco_field, cand_level, skills, recommended_skills,
                courses):
    DB_table_name = 'user_data'
    insert_sql = "insert into " + DB_table_name + """
    values (0,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
    rec_values = (
        name, email, str(res_score), timestamp, str(no_of_pages), reco_field, cand_level, skills, recommended_skills,
        courses)
    cursor.execute(insert_sql, rec_values)
    connection.commit()





def read_docx(file_path):
    doc = docx.Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)








def extract_basic_info(resume_text):
    # Define regular expressions for name, email, mobile number, and LinkedIn
    name_pattern = re.compile(r'[A-Za-z]+ [A-Za-z]+')
    email_pattern = re.compile(r'[\w\.-]+@[\w\.-]+')
    mobile_number_pattern = re.compile(r'\(\d{3}\) \d{3} \d{2} \d{2}')
    linkedin_pattern = re.compile(r'https?://(?:www\.)?linkedin\.com/in/([a-zA-Z0-9_-]+)')

    # Extract information using regular expressions
    name_match = re.search(name_pattern, resume_text)
    email_match = re.search(email_pattern, resume_text)
    mobile_number_match = re.search(mobile_number_pattern, resume_text)
    linkedin_match = re.search(linkedin_pattern, resume_text)

    # Get the extracted values or set to None if not found
    name = name_match.group().strip() if name_match else None
    email = email_match.group().strip() if email_match else None
    mobile_number = mobile_number_match.group().strip() if mobile_number_match else None
    linkedin = linkedin_match.group().strip() if linkedin_match else None

    return name, email, mobile_number, linkedin


def process_docx(file_path):
    # Load the DOCX file
    doc = docx2txt.process(file_path)

    # Extract basic info using the first function
    name, email, mobile_number, linkedin = extract_basic_info(doc)

    # Extracting Address
    address_start = doc.find("Address:")
    address_end = doc.find("Objective")
    address = doc[address_start:address_end].replace("Address:", "").strip()

    # Extracting Objective
    objective_start = doc.find("Objective")
    objective_end = doc.find("Skills")
    objective_section = doc[objective_start:objective_end].replace("Objective", "").strip()

    # Extracting Skills using regular expression
    skills_start = doc.find("Skills")
    skills_end = doc.find("Projects")
    skills_section = doc[skills_start:skills_end]

    # Use regex to find skills (assuming skills are separated by commas)
    skills_list = re.findall(r'\b(?:' + '|'.join(skill_mapping.keys()) + r')\b', skills_section, flags=re.IGNORECASE)

    # Map skills to the specific values mentioned
    skills_tuple = tuple(skill_mapping.get(skill.lower(), skill) for skill in skills_list)

    # Extracting Projects
    projects_start = doc.find("Projects")
    projects_end = doc.find("Education")
    projects_section = doc[projects_start:projects_end].replace("Projects", "").strip()
    num_pages = doc.count("\f") + 1

    return {
        'name': name,
        'email': email,
        'linkedin': linkedin,
        'address': address,
        'objective': objective_section,
        'skills': skills_tuple,
        'projects': projects_section,
        'num_pages': num_pages

    }




st.set_page_config(
    page_title="Smart Resume Analyzer",
    page_icon='./Logo/Logo.jpg',
    layout="wide"
)




def run():
    st.title("Smart Resume Analyser")
    st.sidebar.markdown("# Choose User")
    st.sidebar.markdown("---")
    activities = ["Normal User", "Admin"]
    choice = st.sidebar.selectbox("Choose among the given options:", activities)

    img = Image.open('./Logo/Logo.jpg')
    img = img.resize((250, 250))
    st.image(img)

    # Create the DB
    db_sql = """CREATE DATABASE IF NOT EXISTS sra;"""
    cursor.execute(db_sql)
    connection.select_db("sra")

    # Create table
    DB_table_name = 'user_data'
    table_sql = "CREATE TABLE IF NOT EXISTS " + DB_table_name + """
                    (ID INT NOT NULL AUTO_INCREMENT,
                     Name varchar(100) NOT NULL,
                     Email_ID VARCHAR(50) NOT NULL,
                     resume_score VARCHAR(8) NOT NULL,
                     Timestamp VARCHAR(50) NOT NULL,
                     Page_no VARCHAR(5) NOT NULL,
                     Predicted_Field VARCHAR(25) NOT NULL,
                     User_level VARCHAR(30) NOT NULL,
                     Actual_skills VARCHAR(300) NOT NULL,
                     Recommended_skills VARCHAR(300) NOT NULL,
                     Recommended_courses VARCHAR(600) NOT NULL,
                     PRIMARY KEY (ID));
                    """
    cursor.execute(table_sql)
    if choice == 'Normal User':
        st.markdown(
            """
            <div style='background-color: #3498db; padding: 20px; border-radius: 10px;'>
                <h2 style='text-align: left; color:#ffffff;'>🚀 Upload your resume and get smart recommendations!</h2>
                <p style='text-align: left; font-size: 16px; color: #ecf0f1;'>Unlock personalized insights based on your resume.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        docx_file = st.file_uploader("Choose your Resume", type=["docx"])
        if docx_file is not None:
            with st.spinner('Uploading your Resume....'):
                time.sleep(4)
            save_image_path = './Uploaded_resume/' + docx_file.name
            with open(save_image_path, "wb") as f:
                f.write(docx_file.getbuffer())
            display_docx_content(save_image_path)
            resume_data = docx2txt.process(save_image_path)
            # Get the whole resume data

            name, email, mobile_number,linkedin = extract_basic_info(resume_data)

            with st.expander("Resume Analysis"):

                st.markdown('<h3 style="color: #3498db;">Your Basic Info</h3>',
                            unsafe_allow_html=True)


                st.text("Name: " + (name if name else 'N/A'))
                st.text("Email: " + (email if email else 'N/A'))
                st.text("Mobile Number: " + (mobile_number if mobile_number else 'N/A'))
                st.text("Linkedin: " + (linkedin if linkedin else 'N/A'))
                resume_datas = process_docx (save_image_path)
                num_pages = resume_datas['num_pages']


                cand_level = ''
                if num_pages == 1:
                    cand_level = "Fresher"
                    st.markdown('''<h4 style='text-align: left; color: $d73b5c;'> You are looking Fresher.</h4>''',
                                unsafe_allow_html=True)
                elif num_pages == 2:
                    cand_level = "Experienced"
                    st.markdown('''<h4 style = 'text-align:left; color: #1ed670;'>You are at experience level''',
                                unsafe_allow_html=True)
                resume_datas = process_docx (save_image_path)


                st.markdown('<h2 style = "color:#3498db" > Skills Recommendation 💡 </h2>',unsafe_allow_html=True)
                #             ## Skill shows
                keywords = st_tags(label='### Skills that you have',
                                   text='See our skills recommendation',
                                   value=resume_datas['skills'], key='1')

                ##  recommendation
                ds_keyword = ['tensorflow', 'keras', 'pytorch', 'machine learning', 'deep Learning', 'flask',
                              'streamlit']
                web_keyword = ['react', 'django', 'node jS', 'react js', 'php', 'laravel', 'magento', 'wordpress',
                               'javascript', 'angular js', 'c#', 'flask']
                android_keyword = ['android', 'android development', 'flutter', 'kotlin', 'xml', 'kivy']
                ios_keyword = ['ios', 'ios development', 'swift', 'cocoa', 'cocoa touch', 'xcode']
                uiux_keyword = ['ux', 'adobe xd', 'figma', 'zeplin', 'balsamiq', 'ui', 'prototyping', 'wireframes',
                                'storyframes', 'adobe photoshop', 'photoshop', 'editing', 'adobe illustrator',
                                'illustrator', 'adobe after effects', 'after effects', 'adobe premier pro',
                                'premier pro', 'adobe indesign', 'indesign', 'wireframe', 'solid', 'grasp',
                                'user research', 'user experience']

                recommended_skills = []
                reco_field = ''
                rec_course = ''
                ## Courses recommendation
                for i in resume_datas['skills']:
                    ## Data science recommendation
                    if i.lower() in ds_keyword:
                        print(i.lower())
                        reco_field = 'Data Science'
                        st.success("** Our analysis says you are looking for Data Science Jobs.**")
                        recommended_skills = ['Data Visualization', 'Predictive Analysis', 'Statistical Modeling',
                                              'Data Mining', 'Clustering & Classification', 'Data Analytics',
                                              'Quantitative Analysis', 'Web Scraping', 'ML Algorithms', 'Keras',
                                              'Pytorch', 'Probability', 'Scikit-learn', 'Tensorflow', "Flask",
                                              'Streamlit']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='2')
                        st.markdown(
                            '''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',
                            unsafe_allow_html=True)
                        rec_course = course_recommender(ds_course)
                        break

                    ## Web development recommendation
                    elif i.lower() in web_keyword:
                        print(i.lower())
                        reco_field = 'Web Development'
                        st.success("** Our analysis says you are looking for Web Development Jobs **")
                        recommended_skills = ['React', 'Django', 'Node JS', 'React JS', 'php', 'laravel', 'Magento',
                                              'wordpress', 'Javascript', 'Angular JS', 'c#', 'Flask', 'SDK']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='3')
                        st.markdown(
                            '''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the
                             chances of getting a Job💼</h4>''',
                            unsafe_allow_html=True)
                        rec_course = course_recommender(web_course)
                        break

                    ## Android App Development
                    elif i.lower() in android_keyword:
                        print(i.lower())
                        reco_field = 'Android Development'
                        st.success("** Our analysis says you are looking for Android App Development Jobs **")
                        recommended_skills = ['Android', 'Android development', 'Flutter', 'Kotlin', 'XML', 'Java',
                                              'Kivy', 'GIT', 'SDK', 'SQLite']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='4')
                        st.markdown(
                            '''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀
                             the chances of getting a Job💼</h4>''',
                            unsafe_allow_html=True)
                        rec_course = course_recommender(android_course)
                        break

                    ## IOS App Development
                    elif i.lower() in ios_keyword:
                        print(i.lower())
                        reco_field = 'IOS Development'
                        st.success("** Our analysis says you are looking for IOS App Development Jobs **")
                        recommended_skills = ['IOS', 'IOS Development', 'Swift', 'Cocoa', 'Cocoa Touch', 'Xcode',
                                              'Objective-C', 'SQLite', 'Plist', 'StoreKit', "UI-Kit", 'AV Foundation',
                                              'Auto-Layout']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='5')
                        st.markdown(
                            '''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀
                             the chances of getting a Job💼</h4>''',
                            unsafe_allow_html=True)
                        rec_course = course_recommender(ios_course)
                        break

                    ## Ui-UX Recommendation
                    elif i.lower() in uiux_keyword:
                        print(i.lower())
                        reco_field = 'UI-UX Development'
                        st.success("** Our analysis says you are looking for UI-UX Development Jobs **")
                        recommended_skills = ['UI', 'User Experience', 'Adobe XD', 'Figma', 'Zeplin', 'Balsamiq',
                                              'Prototyping', 'Wireframes', 'Storyframes', 'Adobe Photoshop', 'Editing',
                                              'Illustrator', 'After Effects', 'Premier Pro', 'Indesign', 'Wireframe',
                                              'Solid', 'Grasp', 'User Research']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='6')
                        st.markdown(
                            '''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will 
                            boost🚀 the chances of getting a Job💼</h4>''',
                            unsafe_allow_html=True)
                        rec_course = course_recommender(uiux_course)
                        break

                ts = time.time()
                cur_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                cur_time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
                timestamp = str(cur_date + '_' + cur_time)

                #             ### Resume writing recommendation
                st.subheader("**Resume Tips & Ideas💡**")
                resume_score = 0
                if 'objective' in resume_datas:
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Objective</h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please 
                        add your career objective, it will give your career intention to the Recruiters.</h4>''',
                        unsafe_allow_html=True)

                if 'Declaration' in resume_datas:
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Declaration✍/h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please 
                          add Declaration✍. It will give the assurance that everything written on your resume is true 
                          and fully acknowledged by you</h4>''',
                        unsafe_allow_html=True)
                    #
                if 'Hobbies' or 'Interests' in resume_datas:
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your 
                         Hobbies⚽</h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please 
                         add Hobbies⚽. It will show your personality to the Recruiters and give the assurance that you 
                        are fit for this role or not.</h4>''',
                        unsafe_allow_html=True)

                if 'Work Experience' in resume_data:
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your 
                         Achievements🏅 </h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please 
                        add Achievements🏅. It will show that you are capable for the required position.</h4>''',
                        unsafe_allow_html=True)

                if 'Projects' in resume_datas:
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your 
                           Projects👨‍💻 </h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please 
                        add Projects👨‍💻. It will show that you have done work related the required position or 
                        not.</h4>''',
                        unsafe_allow_html=True)
                #
                st.subheader("**Resume Score📝**")
                st.markdown(
                    """
                        <style>
                            .stProgress > div > div > div > div {
                                background-color: #d73b5c;
                            }
                        </style>""",
                    unsafe_allow_html=True,
                )
                my_bar = st.progress(0)
                score = 0
                for percent_complete in range(resume_score):
                    score += 1
                    time.sleep(0.1)
                    my_bar.progress(percent_complete + 1)
                st.success('** Your Resume Writing Score: ' + str(score) + '**')
                st.warning(
                    "** Note: This score is calculated based on the content that you have added in your Resume. **")
                st.balloons()
                #
                insert_data(name, resume_datas['email'], str(resume_score), timestamp,
                            str(resume_datas['num_pages']), reco_field, cand_level, str(resume_datas['skills']),
                            str(recommended_skills), str(rec_course))

                # Insert into table

        #
        #             ## Resume writing video
                st.header("**Bonus Video for Resume Writing Tips💡**")
                resume_vid = random.choice(resume_videos)
                res_vid_title = fetch_yt_video(resume_vid)
                st.subheader("✅ **" + res_vid_title + "**")
                st.video(resume_vid)
        #            ## Interview Preparation Video
                st.header("**Bonus Video for Interview👨‍💼 Tips💡**")
                interview_vid = random.choice(interview_videos)
                int_vid_title = fetch_yt_video(interview_vid)
                st.subheader("✅ **" + int_vid_title + "**")
                st.video(interview_vid)


                connection.commit()

    else:
    #     ## Admin Side
        st.success('Welcome to Admin Side')
        # st.sidebar.subheader('**ID / Password Required!**')

        ad_user = st.text_input("Username")
        ad_password = st.text_input("Password", type='password')
        if st.button('Login'):


            if ad_user == 'sachin' and ad_password == 'sachin123':

                st.success("Welcome BT3200")
                # Display Data
                cursor.execute('''SELECT*FROM user_data''')
                data = cursor.fetchall()
                st.header("**User's👨‍💻 Data**")
                df = pd.DataFrame(data, columns=['ID', 'Name', 'Email', 'Resume Score', 'Timestamp', 'Total Page',
                                                 'Predicted Field', 'User Level', 'Actual Skills', 'Recommended Skills',
                                                 'Recommended Course'])
                st.dataframe(df)
                st.markdown(get_table_download_link(df, 'User_Data.csv', 'Download Report'), unsafe_allow_html=True)





            else:
                st.error("Wrong ID & Password Provided")



run()
