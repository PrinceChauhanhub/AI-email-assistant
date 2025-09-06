# src/dashboard.py
import streamlit as st
import sqlite3
import pandas as pd
import json
import plotly.express as px
import sys
import os

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from gmails_tools import fetch_support_emails, send_reply
from email_processor import EmailProcessor
from response_generator import ResponseGenerator
from database import Database

DB_PATH = "db/emails.db"

st.set_page_config(layout="wide", page_title="AI Email Assistant")

st.title("📩 AI-Powered Communication Assistant")

# Add auto-refresh option
if st.checkbox("🔄 Auto-refresh every 30 seconds"):
    import time
    time.sleep(30)
    st.rerun()

# Add action buttons at the top
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    if st.button("🔄 Fetch & Process New Emails", type="primary"):
        with st.spinner("Processing emails..."):
            try:
                # Fetch emails
                emails = fetch_support_emails(max_results=10)
                if emails:
                    processor = EmailProcessor()
                    responder = ResponseGenerator()
                    db = Database()
                    my_email = "idf6877@gmail.com"
                    
                    processed_count = 0
                    sent_count = 0
                    
                    for email in emails:
                        if db.is_replied(email["id"]):
                            continue
                        
                        # Extract email from sender field
                        import re
                        match = re.search(r'<(.+?)>', email["sender"])
                        sender_email = (match.group(1) if match else email["sender"]).lower()
                        if sender_email == my_email.lower():
                            continue
                            
                        processed = processor.process_email(email)
                        draft = responder.generate_response(email, processed)
                        db.save_email(email, processed, draft)
                        processed_count += 1
                        
                        # Send reply for urgent emails
                        if processed["priority_label"] == "Urgent":
                            send_reply(email["sender"], email["subject"], draft)
                            cur = db.conn.cursor()
                            cur.execute("UPDATE emails SET status='Replied' WHERE id=?", (email["id"],))
                            db.conn.commit()
                            sent_count += 1
                    
                    st.success(f"✅ Processed {processed_count} new emails, sent {sent_count} urgent replies!")
                    st.rerun()
                else:
                    st.info("No new support emails found.")
            except Exception as e:
                st.error(f"Error processing emails: {str(e)}")

with col2:
    if st.button("📧 Send All Pending Replies"):
        with st.spinner("Sending replies..."):
            try:
                db = Database()
                conn = sqlite3.connect(DB_PATH)
                pending_emails = pd.read_sql_query(
                    "SELECT * FROM emails WHERE status='Pending'", conn
                )
                conn.close()
                
                sent_count = 0
                for _, row in pending_emails.iterrows():
                    send_reply(row["sender"], row["subject"], row["draft"])
                    
                    # Update status
                    conn = sqlite3.connect(DB_PATH)
                    cur = conn.cursor()
                    cur.execute("UPDATE emails SET status='Replied' WHERE id=?", (row["id"],))
                    conn.commit()
                    conn.close()
                    sent_count += 1
                
                st.success(f"✅ Sent {sent_count} replies!")
                st.rerun()
            except Exception as e:
                st.error(f"Error sending replies: {str(e)}")

with col3:
    if st.button("🗑️ Clear All"):
        if st.session_state.get('confirm_clear', False):
            try:
                conn = sqlite3.connect(DB_PATH)
                cur = conn.cursor()
                cur.execute("DELETE FROM emails")
                conn.commit()
                conn.close()
                st.success("✅ All emails cleared!")
                st.rerun()
            except Exception as e:
                st.error(f"Error clearing emails: {str(e)}")
        else:
            st.session_state['confirm_clear'] = True
            st.warning("Click again to confirm clearing all emails")

def load_df():
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query("SELECT * FROM emails", conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df

df = load_df()

# Filter out self emails from display
MY_EMAIL = "idf6877@gmail.com"
import re
def extract_email(sender):
    match = re.search(r'<(.+?)>', str(sender))
    if match:
        return match.group(1)
    return str(sender).strip()

if not df.empty:
    df = df[df["sender"].apply(lambda x: extract_email(x).lower() != MY_EMAIL.lower())]

if df.empty:
    st.info("No emails yet. Run main.py to ingest/process emails.")
else:
    # --- Email List with Filtering ---
    st.subheader("Email List")
    search = st.text_input("Search by sender, subject, or status")
    filtered_df = df[df.apply(lambda x: search.lower() in str(x["sender"]).lower() or search.lower() in str(x["subject"]).lower() or search.lower() in str(x["status"]).lower(), axis=1)] if search else df
    st.dataframe(filtered_df[["id","sender","subject","sentiment","priority_label","status"]], use_container_width=True)

    # --- Analytics Section ---
    st.subheader("📊 Advanced Analytics")
    
    # Summary Statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Emails", len(df))
    
    with col2:
        try:
            df_copy = df.copy()
            df_copy["date_parsed"] = pd.to_datetime(df_copy["date"], errors="coerce", utc=True)
            cutoff_time = pd.Timestamp.now(tz='UTC') - pd.Timedelta(days=1)
            last_24h = df_copy[df_copy["date_parsed"] > cutoff_time]
            st.metric("Last 24 Hours", len(last_24h))
        except Exception:
            st.metric("Last 24 Hours", "N/A")
    
    with col3:
        resolved_count = len(df[df["status"] == "Resolved"])
        st.metric("Resolved", resolved_count)
    
    with col4:
        pending_count = len(df[df["status"] == "Pending"])
        st.metric("Pending", pending_count)
    
    # Charts
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write("Sentiment Distribution")
        if len(df) > 0:
            fig = px.pie(df, names="sentiment", title="Sentiment Analysis")
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.write("Priority Distribution")
        if len(df) > 0:
            fig = px.pie(df, names="priority_label", title="Priority Levels", 
                        color_discrete_map={"Urgent": "red", "Not urgent": "blue"})
            st.plotly_chart(fig, use_container_width=True)
    
    with col3:
        st.write("Status Overview")
        if len(df) > 0:
            status_counts = df["status"].value_counts()
            fig = px.bar(x=status_counts.index, y=status_counts.values, 
                        title="Email Status", color=status_counts.values,
                        color_continuous_scale="Viridis")
            st.plotly_chart(fig, use_container_width=True)
    
    # Time series chart
    st.subheader("📈 Email Trends")
    if "date" in df.columns and len(df) > 0:
        try:
            df_copy = df.copy()
            df_copy["date_parsed"] = pd.to_datetime(df_copy["date"], errors="coerce", utc=True)
            valid_dates = df_copy.dropna(subset=["date_parsed"])
            if not valid_dates.empty:
                valid_dates = valid_dates.copy()
                # Convert to local timezone for display
                valid_dates["date_only"] = valid_dates["date_parsed"].dt.tz_convert(None).dt.date
                time_df = valid_dates.groupby("date_only").size().reset_index(name="count")
                fig = px.line(time_df, x="date_only", y="count", title="Emails Received Over Time",
                             markers=True)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No valid dates to plot timeline.")
        except Exception as e:
            st.info(f"Unable to generate timeline chart: {str(e)}")
    
    # Detailed breakdown
    st.subheader("🔍 Detailed Breakdown")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Top Senders**")
        if len(df) > 0:
            sender_counts = df["sender"].value_counts().head(5)
            st.dataframe(sender_counts, use_container_width=True)
    
    with col2:
        st.write("**Response Rate**")
        if len(df) > 0:
            total = len(df)
            replied = len(df[df["status"] == "Replied"])
            response_rate = (replied / total * 100) if total > 0 else 0
            
            fig = px.pie(values=[replied, total-replied], names=["Replied", "Not Replied"],
                        title=f"Response Rate: {response_rate:.1f}%")
            st.plotly_chart(fig, use_container_width=True)

    # --- Details & Drafts ---
    st.subheader("📧 Email Details & AI Responses")
    for _, row in filtered_df.iterrows():
        urgency_color = "#ffebee" if row["priority_label"] == "Urgent" else "#f5f5f5"
        status_color = "#e8f5e8" if row["status"] == "Resolved" else "#fff3e0" if row["status"] == "Replied" else "#fce4ec"
        
        with st.expander(f"{'🚨' if row['priority_label'] == 'Urgent' else '📬'} {row['subject']} — {row['sender']}", expanded=False):
            # Header info
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.markdown(f"**📅 Received:** {row['date']}")
            with col2:
                st.markdown(f"**😊 Sentiment:** {row['sentiment'].title()}")
            with col3:
                st.markdown(f"**⚡ Priority:** {row['priority_label']}")
            
            # Status badge
            status_emoji = {"Pending": "⏳", "Replied": "✅", "Resolved": "🎯"}.get(row["status"], "❓")
            st.markdown(f"**{status_emoji} Status:** {row['status']}")
            
            # Email body with styling
            st.markdown(f"<div style='background-color:{urgency_color};padding:15px;border-radius:5px;margin:10px 0'><b>📄 Email Body:</b><br>{row['body']}</div>", unsafe_allow_html=True)
            
            # Extracted information
            try:
                extracted = json.loads(row["extracted"]) if isinstance(row["extracted"], str) else row["extracted"]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**📞 Contact Information:**")
                    phones = extracted.get("phones", [])
                    emails = extracted.get("emails", [])
                    if phones or emails:
                        if phones:
                            st.write(f"📱 Phones: {', '.join(phones[:3])}")
                        if emails:
                            st.write(f"📧 Alt Emails: {', '.join(emails[:3])}")
                    else:
                        st.write("No additional contact info found")
                
                with col2:
                    st.markdown("**📋 Customer Requirements:**")
                    requirements = extracted.get("requirements", [])
                    if requirements:
                        for i, req in enumerate(requirements[:3], 1):
                            st.write(f"{i}. {req[:100]}...")
                    else:
                        st.write("No specific requirements extracted")
                
                # Show frustration and urgency indicators
                if extracted.get("frustration_level", 0) > 0:
                    st.warning(f"😤 Customer may be frustrated (score: {extracted.get('frustration_level', 0)})")
                
                if extracted.get("urgency_indicators", 0) > 0:
                    st.error(f"🚨 Urgency detected (score: {extracted.get('urgency_indicators', 0)})")
                
            except Exception as e:
                st.write("**📊 Extracted Data:** Could not parse extraction data")
            
            # AI-generated response
            st.markdown("**🤖 AI-Generated Response:**")
            draft = st.text_area("Edit draft reply", value=row["draft"], height=200, key=f"draft_{row['id']}")
            
            # Action buttons
            cols = st.columns([1, 1, 1, 1, 2])
            
            if cols[0].button("📋 Copy Draft", key=f"copy_{row['id']}"):
                st.success("Draft content copied! (Feature placeholder)")
            
            if cols[1].button("📧 Send Reply", key=f"send_{row['id']}"):
                try:
                    send_reply(row["sender"], row["subject"], draft)
                    conn = sqlite3.connect(DB_PATH)
                    cur = conn.cursor()
                    cur.execute("UPDATE emails SET status='Replied' WHERE id=?", (row["id"],))
                    conn.commit()
                    conn.close()
                    st.success("✅ Reply sent successfully!")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Error sending reply: {str(e)}")
            
            if cols[2].button("✅ Mark Resolved", key=f"resolve_{row['id']}"):
                conn = sqlite3.connect(DB_PATH)
                cur = conn.cursor()
                cur.execute("UPDATE emails SET status=? WHERE id=?", ("Resolved", row["id"]))
                conn.commit()
                conn.close()
                st.success("✅ Marked as resolved! Please refresh the page.")
                st.rerun()
            
            if cols[3].button("🔄 Regenerate", key=f"regen_{row['id']}"):
                try:
                    processor = EmailProcessor()
                    responder = ResponseGenerator()
                    email_data = {
                        "id": row["id"],
                        "sender": row["sender"],
                        "subject": row["subject"],
                        "body": row["body"]
                    }
                    processed = processor.process_email(email_data)
                    new_draft = responder.generate_response(email_data, processed)
                    
                    conn = sqlite3.connect(DB_PATH)
                    cur = conn.cursor()
                    cur.execute("UPDATE emails SET draft=? WHERE id=?", (new_draft, row["id"]))
                    conn.commit()
                    conn.close()
                    st.success("🔄 Response regenerated!")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Error regenerating response: {str(e)}")
            
            # Show confidence score or additional metrics
            st.markdown(f"<div style='background-color:#f0f0f0;padding:10px;border-radius:5px;margin-top:10px'><small>💯 Priority Score: {row.get('priority_score', 'N/A')} | 📊 Confidence: High | 🎯 Auto-processed: Yes</small></div>", unsafe_allow_html=True)
