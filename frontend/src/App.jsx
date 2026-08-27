import { useState, useEffect } from "react";
import Upload from "./components/Upload";
import EventFeed from "./components/EventFeed";
import LiveMonitor from "./components/LiveMonitor";
import { getJob, getJobEvents, listJobs, FILES_BASE } from "./api";

function NavBar() {
  function scrollTo(id) {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
  }
  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <div className="brand">
          <span className="brand-mark" />
          TheftGuard
        </div>
        <div className="nav-links">
          <button onClick={() => scrollTo("how-it-works")}>How it works</button>
          <button onClick={() => scrollTo("features")}>Features</button>
          <button className="nav-cta" onClick={() => scrollTo("try-it")}>Analyze footage</button>
        </div>
      </div>
    </nav>
  );
}

function Hero() {
  function scrollTo(id) {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
  }
  return (
    <header className="hero">
      <span className="eyebrow">Video theft detection</span>
      <h1>Turn ordinary footage into an early warning system</h1>
      <p className="hero-sub">
        TheftGuard analyzes video for object and person tracking, then flags patterns
        commonly linked to theft — items disappearing, unattended concealment, prolonged
        loitering — so you don't have to watch every frame yourself.
      </p>
      <div className="hero-actions">
        <button className="btn-primary" onClick={() => scrollTo("try-it")}>Analyze a video</button>
        <button className="btn-secondary" onClick={() => scrollTo("how-it-works")}>See how it works</button>
      </div>
    </header>
  );
}

function HowItWorks() {
  const steps = [
    { n: "01", title: "Upload footage", body: "Drop in a clip from any existing camera. No special hardware or new installation required." },
    { n: "02", title: "AI tracks every object", body: "Detection and tracking identify people and items frame by frame, building a full movement history." },
    { n: "03", title: "Suspicious patterns are flagged", body: "Rules run against that history to surface disappearances, likely removals, and loitering, ranked by severity." },
  ];
  return (
    <section id="how-it-works" className="section">
      <h2 className="section-title">How it works</h2>
      <div className="steps">
        {steps.map((s) => (
          <div className="step" key={s.n}>
            <span className="step-num">{s.n}</span>
            <h3>{s.title}</h3>
            <p>{s.body}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function Features() {
  const items = [
    { title: "Object + person tracking", body: "Every detected item and person gets a persistent ID across the whole clip, not just a single-frame box." },
    { title: "Pattern-based flagging", body: "Object disappearance, likely removal linked to a person, and loitering are detected from movement data, not guesswork." },
    { title: "Works with existing footage", body: "No proprietary cameras needed — analyze any video file you already have." },
    { title: "Runs on your own machine", body: "Processing happens locally through your own backend. Footage isn't sent to a third party." },
    { title: "Event timeline", body: "Every flagged moment is timestamped and explained, so review takes seconds instead of scrubbing the whole video." },
    { title: "Adjustable sensitivity", body: "Detection thresholds are plain constants you can tune to your own camera angle and environment." },
  ];
  return (
    <section id="features" className="section">
      <h2 className="section-title">Built for review, not just recording</h2>
      <div className="feature-grid">
        {items.map((f) => (
          <div className="feature-card" key={f.title}>
            <h3>{f.title}</h3>
            <p>{f.body}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function PastAnalyses({ jobs, onSelect }) {
  if (!jobs || jobs.length === 0) return null;
  return (
    <div className="past-analyses">
      <h3 className="results-heading">Recent analyses</h3>
      <div className="job-list">
        {jobs.map((j) => (
          <button key={j.id} className="job-item" onClick={() => onSelect(j.id)}>
            <span className={`job-status job-status-${j.status}`}>{j.status}</span>
            <span className="job-name">{j.original_filename}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

function TryIt({ job, events, jobs, onJobReady, onSelectJob }) {
  const [subMode, setSubMode] = useState("upload");

  return (
    <section id="try-it" className="section try-it">
      <h2 className="section-title">Analyze footage</h2>
      <p className="section-sub">Upload a clip, or monitor a live camera feed in real time.</p>

      <div className="subtabs">
        <button className={subMode === "upload" ? "active" : ""} onClick={() => setSubMode("upload")}>
          Upload video
        </button>
        <button className={subMode === "live" ? "active" : ""} onClick={() => setSubMode("live")}>
          Live camera
        </button>
      </div>

      {subMode === "upload" && (
        <>
          <Upload onJobReady={onJobReady} />

          {job && job.status === "done" && (
            <div className="results">
              <video controls src={`${FILES_BASE}${job.tracked_video_url}`} className="result-video" />
              <h3 className="results-heading">Flagged events</h3>
              <EventFeed events={events} />
            </div>
          )}

          {job && job.status === "failed" && (
            <p className="error-text">Processing failed for this video. Check the backend terminal for details.</p>
          )}

          <PastAnalyses jobs={jobs} onSelect={onSelectJob} />
        </>
      )}

      {subMode === "live" && <LiveMonitor />}
    </section>
  );
}

export default function App() {
  const [job, setJob] = useState(null);
  const [events, setEvents] = useState([]);
  const [jobs, setJobs] = useState([]);

  async function refreshJobList() {
    const data = await listJobs();
    setJobs(data);
  }

  useEffect(() => {
    refreshJobList();
  }, []);

  async function loadJob(jobId) {
    const jobData = await getJob(jobId);
    const eventData = await getJobEvents(jobId);
    setJob(jobData);
    setEvents(eventData);
  }

  async function handleJobReady(jobId) {
    await loadJob(jobId);
    await refreshJobList();
  }

  return (
    <div className="app">
      <NavBar />
      <Hero />
      <HowItWorks />
      <Features />
      <TryIt job={job} events={events} jobs={jobs} onJobReady={handleJobReady} onSelectJob={loadJob} />
      <footer className="footer">
        <span>TheftGuard — video analysis for theft-pattern detection</span>
      </footer>
    </div>
  );
}