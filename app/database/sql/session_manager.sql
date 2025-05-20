--
-- PostgreSQL database dump
--

-- Dumped from database version 17.5
-- Dumped by pg_dump version 17.5

-- Started on 2025-05-20 11:01:55

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 6 (class 2615 OID 16389)
-- Name: session_manager; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA session_manager;


ALTER SCHEMA session_manager OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 220 (class 1259 OID 16434)
-- Name: message; Type: TABLE; Schema: session_manager; Owner: postgres
--

CREATE TABLE session_manager.message (
    content text NOT NULL,
    author text NOT NULL,
    message_timestamp timestamp(0) with time zone NOT NULL,
    session_id integer NOT NULL
);


ALTER TABLE session_manager.message OWNER TO postgres;

--
-- TOC entry 219 (class 1259 OID 16391)
-- Name: session; Type: TABLE; Schema: session_manager; Owner: postgres
--

CREATE TABLE session_manager.session (
    session_id integer NOT NULL,
    session_name text NOT NULL,
    description text,
    map_name text NOT NULL,
    start_date date NOT NULL,
    start_time timestamp(0) with time zone NOT NULL
);


ALTER TABLE session_manager.session OWNER TO postgres;

--
-- TOC entry 218 (class 1259 OID 16390)
-- Name: session_manager_session_id_seq; Type: SEQUENCE; Schema: session_manager; Owner: postgres
--

ALTER TABLE session_manager.session ALTER COLUMN session_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME session_manager.session_manager_session_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 4852 (class 0 OID 16434)
-- Dependencies: 220
-- Data for Name: message; Type: TABLE DATA; Schema: session_manager; Owner: postgres
--

COPY session_manager.message (content, author, message_timestamp, session_id) FROM stdin;
\.


--
-- TOC entry 4851 (class 0 OID 16391)
-- Dependencies: 219
-- Data for Name: session; Type: TABLE DATA; Schema: session_manager; Owner: postgres
--

COPY session_manager.session (session_id, session_name, description, map_name, start_date, start_time) FROM stdin;
\.


--
-- TOC entry 4858 (class 0 OID 0)
-- Dependencies: 218
-- Name: session_manager_session_id_seq; Type: SEQUENCE SET; Schema: session_manager; Owner: postgres
--

SELECT pg_catalog.setval('session_manager.session_manager_session_id_seq', 1, false);


--
-- TOC entry 4703 (class 2606 OID 16440)
-- Name: message message_pkey; Type: CONSTRAINT; Schema: session_manager; Owner: postgres
--

ALTER TABLE ONLY session_manager.message
    ADD CONSTRAINT message_pkey PRIMARY KEY (session_id);


--
-- TOC entry 4701 (class 2606 OID 16395)
-- Name: session session_manager_pkey; Type: CONSTRAINT; Schema: session_manager; Owner: postgres
--

ALTER TABLE ONLY session_manager.session
    ADD CONSTRAINT session_manager_pkey PRIMARY KEY (session_id);


--
-- TOC entry 4704 (class 2606 OID 16441)
-- Name: message message_session_id_fkey; Type: FK CONSTRAINT; Schema: session_manager; Owner: postgres
--

ALTER TABLE ONLY session_manager.message
    ADD CONSTRAINT message_session_id_fkey FOREIGN KEY (session_id) REFERENCES session_manager.session(session_id);


-- Completed on 2025-05-20 11:01:56

--
-- PostgreSQL database dump complete
--

