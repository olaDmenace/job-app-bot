-- -- Jobs table to store basic job information
-- CREATE TABLE jobs (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     job_source_id TEXT,           -- ID from the source (e.g., web3.career job id)
--     source TEXT,                  -- Where the job was found (e.g., "web3.career")
--     title TEXT NOT NULL,
--     company TEXT NOT NULL,
--     location TEXT,
--     salary TEXT,
--     url TEXT,
--     tags TEXT,                    -- Stored as comma-separated values
--     date_posted TEXT,             -- Original posting date
--     date_found TEXT NOT NULL,     -- When our scraper found it
--     description TEXT,             -- Full job description
--     is_remote BOOLEAN,
--     UNIQUE(job_source_id, source) -- Prevent duplicates from same source
-- );

-- -- Application status tracking
-- CREATE TABLE applications (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     job_id INTEGER NOT NULL,
--     status TEXT NOT NULL DEFAULT 'New',  -- New, Interested, Applied, Interviewing, Rejected, Offer
--     date_applied TEXT,
--     resume_version TEXT,          -- Path or reference to resume used
--     cover_letter_version TEXT,    -- Path or reference to cover letter used
--     application_platform TEXT,    -- Where you actually applied (Company site, LinkedIn, etc.)
--     next_followup_date TEXT,
--     notes TEXT,
--     last_updated TEXT NOT NULL,
--     FOREIGN KEY (job_id) REFERENCES jobs(id),
--     CHECK (status IN ('New', 'Interested', 'Applied', 'Interviewing', 'Rejected', 'Offer'))
-- );

-- -- Contacts associated with applications
-- CREATE TABLE contacts (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     application_id INTEGER NOT NULL,
--     name TEXT NOT NULL,
--     role TEXT,
--     email TEXT,
--     phone TEXT,
--     linkedin_url TEXT,
--     notes TEXT,
--     FOREIGN KEY (application_id) REFERENCES applications(id)
-- );

-- -- Interview tracking
-- CREATE TABLE interviews (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     application_id INTEGER NOT NULL,
--     interview_date TEXT NOT NULL,
--     interview_type TEXT,          -- Phone, Video, Onsite, Technical, etc.
--     interviewer_names TEXT,
--     preparation_notes TEXT,
--     feedback_notes TEXT,
--     next_steps TEXT,
--     FOREIGN KEY (application_id) REFERENCES applications(id)
-- );

-- -- Reminders and tasks
-- CREATE TABLE reminders (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     application_id INTEGER NOT NULL,
--     reminder_date TEXT NOT NULL,
--     reminder_type TEXT,           -- Follow-up, Thank you note, etc.
--     description TEXT,
--     is_completed BOOLEAN DEFAULT 0,
--     FOREIGN KEY (application_id) REFERENCES applications(id)
-- );

-- -- Salary discussions
-- CREATE TABLE salary_discussions (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     application_id INTEGER NOT NULL,
--     discussion_date TEXT NOT NULL,
--     base_salary REAL,
--     bonus REAL,
--     equity TEXT,
--     benefits TEXT,
--     notes TEXT,
--     FOREIGN KEY (application_id) REFERENCES applications(id)
-- );


-- -- Companies table for additional company information
-- CREATE TABLE companies (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     name TEXT NOT NULL,
--     website TEXT,
--     industry TEXT,
--     company_size TEXT,
--     funding_stage TEXT,
--     tech_stack TEXT,              -- Comma-separated list of technologies
--     notes TEXT,
--     linkedin_url TEXT,
--     wellfound_url TEXT,
--     last_updated TEXT NOT NULL,
--     UNIQUE(name, website)
-- );

-- -- Professional contacts for cold outreach
-- CREATE TABLE outreach_contacts (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     company_id INTEGER,
--     name TEXT NOT NULL,
--     title TEXT,
--     email TEXT,
--     linkedin_url TEXT,
--     wellfound_url TEXT,
--     source TEXT,                  -- Where we found this contact (LinkedIn, WellFound, etc.)
--     is_hiring_manager BOOLEAN,
--     is_technical BOOLEAN,
--     last_updated TEXT NOT NULL,
--     notes TEXT,
--     FOREIGN KEY (company_id) REFERENCES companies(id)
-- );

-- -- Email templates for different outreach scenarios
-- CREATE TABLE email_templates (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     name TEXT NOT NULL,           -- Template identifier
--     subject TEXT NOT NULL,
--     body TEXT NOT NULL,
--     use_case TEXT,               -- Initial outreach, follow-up, etc.
--     variables TEXT,              -- JSON string of required variables
--     created_at TEXT NOT NULL,
--     last_used TEXT,
--     success_rate REAL            -- Track template performance
-- );

-- -- Track all outreach attempts
-- CREATE TABLE outreach_messages (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     contact_id INTEGER NOT NULL,
--     template_id INTEGER,
--     subject TEXT NOT NULL,
--     message TEXT NOT NULL,
--     sent_date TEXT NOT NULL,
--     status TEXT NOT NULL,         -- Sent, Opened, Replied, No Response
--     response_date TEXT,
--     response_type TEXT,           -- Positive, Negative, Neutral
--     follow_up_count INTEGER DEFAULT 0,
--     next_follow_up_date TEXT,
--     notes TEXT,
--     FOREIGN KEY (contact_id) REFERENCES outreach_contacts(id),
--     FOREIGN KEY (template_id) REFERENCES email_templates(id)
-- );

-- -- Track relationships between jobs and outreach
-- CREATE TABLE job_outreach_links (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     job_id INTEGER NOT NULL,
--     outreach_message_id INTEGER NOT NULL,
--     relationship_type TEXT,       -- Direct application, Referral, etc.
--     notes TEXT,
--     FOREIGN KEY (job_id) REFERENCES jobs(id),
--     FOREIGN KEY (outreach_message_id) REFERENCES outreach_messages(id)
-- );

-- -- Track networking events and conversations
-- CREATE TABLE networking_events (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     company_id INTEGER,
--     contact_id INTEGER,
--     event_type TEXT,             -- Coffee chat, Tech meetup, Conference, etc.
--     event_date TEXT NOT NULL,
--     location TEXT,
--     notes TEXT,
--     follow_up_notes TEXT,
--     next_steps TEXT,
--     FOREIGN KEY (company_id) REFERENCES companies(id),
--     FOREIGN KEY (contact_id) REFERENCES outreach_contacts(id)
-- );

-- -- Add indexes for better performance
-- CREATE INDEX idx_companies_name ON companies(name);
-- CREATE INDEX idx_outreach_contacts_email ON outreach_contacts(email);
-- CREATE INDEX idx_outreach_messages_sent_date ON outreach_messages(sent_date);
-- CREATE INDEX idx_messages_status ON outreach_messages(status);


CREATE TABLE IF NOT EXISTS jobs (
   id INTEGER PRIMARY KEY AUTOINCREMENT,
   job_source_id TEXT,
   source TEXT,
   title TEXT NOT NULL,
   company TEXT NOT NULL, 
   location TEXT,
   salary TEXT,
   url TEXT,
   tags TEXT,
   date_posted TEXT,
   date_found TEXT NOT NULL,
   description TEXT,
   is_remote BOOLEAN,
   UNIQUE(job_source_id, source)
);

CREATE TABLE IF NOT EXISTS applications (
   id INTEGER PRIMARY KEY AUTOINCREMENT,
   job_id INTEGER NOT NULL,
   status TEXT NOT NULL DEFAULT 'New',
   date_applied TEXT,
   resume_version TEXT,
   cover_letter_version TEXT,
   application_platform TEXT,
   next_followup_date TEXT,
   notes TEXT,
   last_updated TEXT NOT NULL,
   FOREIGN KEY (job_id) REFERENCES jobs(id),
   CHECK (status IN ('New', 'Interested', 'Applied', 'Interviewing', 'Rejected', 'Offer'))
);

CREATE TABLE IF NOT EXISTS contacts (
   id INTEGER PRIMARY KEY AUTOINCREMENT,
   application_id INTEGER NOT NULL,
   name TEXT NOT NULL,
   role TEXT,
   email TEXT,
   phone TEXT,
   linkedin_url TEXT,
   notes TEXT,
   FOREIGN KEY (application_id) REFERENCES applications(id)
);

CREATE TABLE IF NOT EXISTS interviews (
   id INTEGER PRIMARY KEY AUTOINCREMENT,
   application_id INTEGER NOT NULL,
   interview_date TEXT NOT NULL,
   interview_type TEXT,
   interviewer_names TEXT,
   preparation_notes TEXT,
   feedback_notes TEXT,
   next_steps TEXT,
   FOREIGN KEY (application_id) REFERENCES applications(id)
);

CREATE TABLE IF NOT EXISTS reminders (
   id INTEGER PRIMARY KEY AUTOINCREMENT,
   application_id INTEGER NOT NULL,
   reminder_date TEXT NOT NULL,
   reminder_type TEXT,
   description TEXT,
   is_completed BOOLEAN DEFAULT 0,
   FOREIGN KEY (application_id) REFERENCES applications(id)
);

CREATE TABLE IF NOT EXISTS salary_discussions (
   id INTEGER PRIMARY KEY AUTOINCREMENT,
   application_id INTEGER NOT NULL,
   discussion_date TEXT NOT NULL,
   base_salary REAL,
   bonus REAL,
   equity TEXT,
   benefits TEXT,
   notes TEXT,
   FOREIGN KEY (application_id) REFERENCES applications(id)
);

CREATE TABLE IF NOT EXISTS companies (
   id INTEGER PRIMARY KEY AUTOINCREMENT,
   name TEXT NOT NULL,
   website TEXT,
   industry TEXT,
   company_size TEXT,
   funding_stage TEXT,
   tech_stack TEXT,
   notes TEXT,
   linkedin_url TEXT,
   wellfound_url TEXT,
   last_updated TEXT NOT NULL,
   UNIQUE(name, website)
);

CREATE TABLE IF NOT EXISTS outreach_contacts (
   id INTEGER PRIMARY KEY AUTOINCREMENT,
   company_id INTEGER,
   name TEXT NOT NULL,
   title TEXT,
   email TEXT,
   linkedin_url TEXT,
   wellfound_url TEXT,
   source TEXT,
   is_hiring_manager BOOLEAN,
   is_technical BOOLEAN,
   last_updated TEXT NOT NULL,
   notes TEXT,
   FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE IF NOT EXISTS email_templates (
   id INTEGER PRIMARY KEY AUTOINCREMENT,
   name TEXT NOT NULL,
   subject TEXT NOT NULL,
   body TEXT NOT NULL,
   use_case TEXT,
   variables TEXT,
   created_at TEXT NOT NULL,
   last_used TEXT,
   success_rate REAL
);

CREATE TABLE IF NOT EXISTS outreach_messages (
   id INTEGER PRIMARY KEY AUTOINCREMENT,
   contact_id INTEGER NOT NULL,
   template_id INTEGER,
   subject TEXT NOT NULL,
   message TEXT NOT NULL,
   sent_date TEXT NOT NULL,
   status TEXT NOT NULL,
   response_date TEXT,
   response_type TEXT,
   follow_up_count INTEGER DEFAULT 0,
   next_follow_up_date TEXT,
   notes TEXT,
   FOREIGN KEY (contact_id) REFERENCES outreach_contacts(id),
   FOREIGN KEY (template_id) REFERENCES email_templates(id)
);

CREATE TABLE IF NOT EXISTS job_outreach_links (
   id INTEGER PRIMARY KEY AUTOINCREMENT,
   job_id INTEGER NOT NULL,
   outreach_message_id INTEGER NOT NULL,
   relationship_type TEXT,
   notes TEXT,
   FOREIGN KEY (job_id) REFERENCES jobs(id),
   FOREIGN KEY (outreach_message_id) REFERENCES outreach_messages(id)
);

CREATE TABLE IF NOT EXISTS networking_events (
   id INTEGER PRIMARY KEY AUTOINCREMENT,
   company_id INTEGER,
   contact_id INTEGER,
   event_type TEXT,
   event_date TEXT NOT NULL,
   location TEXT,
   notes TEXT,
   follow_up_notes TEXT,
   next_steps TEXT,
   FOREIGN KEY (company_id) REFERENCES companies(id),
   FOREIGN KEY (contact_id) REFERENCES outreach_contacts(id)
);

CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(name);
CREATE INDEX IF NOT EXISTS idx_outreach_contacts_email ON outreach_contacts(email);
CREATE INDEX IF NOT EXISTS idx_outreach_messages_sent_date ON outreach_messages(sent_date);
CREATE INDEX IF NOT EXISTS idx_messages_status ON outreach_messages(status);