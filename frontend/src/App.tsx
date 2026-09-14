import { useState } from "react";
import LoginForm from "./components/LoginForm";
import ChatWindow from "./components/ChatWindow";

import "./App.css";


function App() {
  const [token, setToken] = useState<string | null>(
    sessionStorage.getItem("access_token")
  );

  function handleLogout() {
    sessionStorage.removeItem("access_token");
    setToken(null);
  }
/*
  function handleSessionExpired() {
    sessionStorage.removeItem("access_token");
    setToken(null);
  }
*/

  if (!token) {
    return (
      <div className="landing-page">
        <section className="hero-section">
          <div className="hero-content">
            <p className="hero-badge">
              Multi-Document RAG Application
            </p>

            <h1>
              Personal RAG Chatbot
            </h1>

            <p className="hero-description">
              Ask natural-language questions across
              multiple PDF documents using retrieval-
              augmented generation.
            </p>

            <div className="hero-tech">
              <span>React</span>
              <span>FastAPI</span>
              <span>Pinecone</span>
              <span>OpenAI</span>
              <span>LangChain</span>
            </div>

            <a
              href="#login"
              className="hero-button"
            >
              Sign in
            </a>
          </div>

          <div className="demo-card">
            <div className="demo-header">
              Demo conversation
            </div>

            <div className="demo-message user-demo">
              What is reinforcement learning?
            </div>

            <div className="demo-message assistant-demo">
              Reinforcement learning is a machine
              learning approach in which an agent
              learns by interacting with an
              environment and receiving rewards.
            </div>

            <div className="demo-message user-demo">
              How is it different from supervised
              learning?
            </div>

            <div className="demo-message assistant-demo">
              Unlike supervised learning, reinforcement
              learning learns from rewards and
              interaction rather than labeled examples.
            </div>
          </div>
        </section>

        <section className="features-section">
          <h2>Project Features</h2>

          <div className="feature-grid">
            <div className="feature-card">
              <h3>Multi-Document RAG</h3>
              <p>
                Retrieves relevant chunks from multiple
                PDF documents using vector search.
              </p>
            </div>

            <div className="feature-card">
              <h3>Streaming Responses</h3>
              <p>
                FastAPI SSE streaming delivers answers
                token by token to the React frontend.
              </p>
            </div>

            <div className="feature-card">
              <h3>Conversation Context</h3>
              <p>
                Follow-up questions use conversation
                history and query rewriting.
              </p>
            </div>

            <div className="feature-card">
              <h3>Incremental Ingestion</h3>
              <p>
                PDF hashing avoids unnecessarily
                re-embedding unchanged documents.
              </p>
            </div>

            <div className="feature-card">
              <h3>Authentication</h3>
              <p>
                JWT-protected FastAPI endpoints with
                session-expiration handling.
              </p>
            </div>

            <div className="feature-card">
              <h3>Two Frontends</h3>
              <p>
                React for the production-style UI and
                Streamlit for rapid experimentation.
              </p>
            </div>
          </div>
        </section>

        <section
          id="login"
          className="login-section"
        >
          <LoginForm onLogin={setToken} />
        </section>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1 className="app-title">
          Personal RAG Chatbot
        </h1>

        <button 
          className="logout-button"
          onClick={handleLogout}
        >
          Logout
        </button>
      </header>

      <main className="app-main">
        <ChatWindow 
          onSessionExpired={handleLogout}
        />
      </main>
    </div>
  );
}

export default App;


// import heroImg from './assets/hero.png'
// import reactLogo from './assets/react.svg'
// import viteLogo from './assets/vite.svg'
// import './App.css'

// function App() {
//   const [count, setCount] = useState(0)

//   return (
//     <>
//       <section id="center">
//         <div className="hero">
//           <img src={heroImg} className="base" width="170" height="179" alt="" />
//           <img src={reactLogo} className="framework" alt="React logo" />
//           <img src={viteLogo} className="vite" alt="Vite logo" />
//         </div>
//         <div>
//           <h1>Get started</h1>
//           <p>
//             Edit <code>src/App.tsx</code> and save to test <code>HMR</code>
//           </p>
//         </div>
//         <button
//           type="button"
//           className="counter"
//           onClick={() => setCount((count) => count + 1)}
//         >
//           Count is {count}
//         </button>
//       </section>

//       <div className="ticks"></div>

//       <section id="next-steps">
//         <div id="docs">
//           <svg className="icon" role="presentation" aria-hidden="true">
//             <use href="/icons.svg#documentation-icon"></use>
//           </svg>
//           <h2>Documentation</h2>
//           <p>Your questions, answered</p>
//           <ul>
//             <li>
//               <a href="https://vite.dev/" target="_blank">
//                 <img className="logo" src={viteLogo} alt="" />
//                 Explore Vite
//               </a>
//             </li>
//             <li>
//               <a href="https://react.dev/" target="_blank">
//                 <img className="button-icon" src={reactLogo} alt="" />
//                 Learn more
//               </a>
//             </li>
//           </ul>
//         </div>
//         <div id="social">
//           <svg className="icon" role="presentation" aria-hidden="true">
//             <use href="/icons.svg#social-icon"></use>
//           </svg>
//           <h2>Connect with us</h2>
//           <p>Join the Vite community</p>
//           <ul>
//             <li>
//               <a href="https://github.com/vitejs/vite" target="_blank">
//                 <svg
//                   className="button-icon"
//                   role="presentation"
//                   aria-hidden="true"
//                 >
//                   <use href="/icons.svg#github-icon"></use>
//                 </svg>
//                 GitHub
//               </a>
//             </li>
//             <li>
//               <a href="https://chat.vite.dev/" target="_blank">
//                 <svg
//                   className="button-icon"
//                   role="presentation"
//                   aria-hidden="true"
//                 >
//                   <use href="/icons.svg#discord-icon"></use>
//                 </svg>
//                 Discord
//               </a>
//             </li>
//             <li>
//               <a href="https://x.com/vite_js" target="_blank">
//                 <svg
//                   className="button-icon"
//                   role="presentation"
//                   aria-hidden="true"
//                 >
//                   <use href="/icons.svg#x-icon"></use>
//                 </svg>
//                 X.com
//               </a>
//             </li>
//             <li>
//               <a href="https://bsky.app/profile/vite.dev" target="_blank">
//                 <svg
//                   className="button-icon"
//                   role="presentation"
//                   aria-hidden="true"
//                 >
//                   <use href="/icons.svg#bluesky-icon"></use>
//                 </svg>
//                 Bluesky
//               </a>
//             </li>
//           </ul>
//         </div>
//       </section>

//       <div className="ticks"></div>
//       <section id="spacer"></section>
//     </>
//   )
// }

// export default App
