-- Basic schema for Public Online Service Provider

CREATE TABLE categories (
  id serial PRIMARY KEY,
  name varchar(200) UNIQUE NOT NULL
);

CREATE TABLE services (
  id serial PRIMARY KEY,
  name varchar(300) NOT NULL,
  description text,
  price_inr double precision DEFAULT 0.0,
  keywords varchar(500),
  category_id integer REFERENCES categories(id),
  is_active boolean DEFAULT true,
  created_at timestamp with time zone DEFAULT now()
);

CREATE TABLE users (
  id serial PRIMARY KEY,
  email varchar(200) UNIQUE NOT NULL,
  password_hash varchar(500) NOT NULL,
  is_admin boolean DEFAULT false,
  created_at timestamp with time zone DEFAULT now()
);

CREATE TABLE orders (
  id serial PRIMARY KEY,
  order_code varchar(50) UNIQUE NOT NULL,
  client_name varchar(200) NOT NULL,
  phone varchar(50) NOT NULL,
  email varchar(200),
  contact_method varchar(50),
  service_id integer REFERENCES services(id),
  user_id integer REFERENCES users(id),
  description text,
  fee_inr double precision DEFAULT 0.0,
  status varchar(50) DEFAULT 'New',
  created_at timestamp with time zone DEFAULT now()
);

-- Order status history
CREATE TABLE order_status_history (
  id serial PRIMARY KEY,
  order_id integer REFERENCES orders(id) NOT NULL,
  previous_status varchar(50),
  new_status varchar(50),
  changed_by varchar(200),
  note text,
  created_at timestamp with time zone DEFAULT now()
);

-- Reviews
CREATE TABLE reviews (
  id serial PRIMARY KEY,
  order_id integer REFERENCES orders(id),
  rating integer NOT NULL,
  comment text,
  client_name varchar(200),
  is_public boolean DEFAULT false,
  created_at timestamp with time zone DEFAULT now()
);

-- Grievances
CREATE TABLE grievances (
  id serial PRIMARY KEY,
  grievance_code varchar(50) UNIQUE NOT NULL,
  order_id integer REFERENCES orders(id),
  client_name varchar(200) NOT NULL,
  phone varchar(50) NOT NULL,
  email varchar(200),
  description text,
  status varchar(50) DEFAULT 'New',
  created_at timestamp with time zone DEFAULT now()
);

-- Attachments (file uploads)
CREATE TABLE attachments (
  id serial PRIMARY KEY,
  order_id integer REFERENCES orders(id),
  filename varchar(300) NOT NULL,
  stored_path varchar(1000) NOT NULL,
  uploaded_by integer REFERENCES users(id),
  created_at timestamp with time zone DEFAULT now()
);

