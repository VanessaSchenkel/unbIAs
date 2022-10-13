import { useNavigate } from "react-router-dom";

import logoImg from "../assets/translator.png";

import "../styles/header.css";

export function Header() {
  const navigate = useNavigate();

  function handleClickGoHome() {
    navigate("/");
  }

  function handleClickGoSobre() {
    navigate("/sobre");
  }

  function handleClickGoContato() {
    navigate("/contato");
  }

  return (
    <div id='header'>
      <button onClick={handleClickGoHome} className='link-home'>
        <img src={logoImg} alt='Logo To bias' />
        <h2>To bIAs</h2>
      </button>
      <div className='header-links'>
        <button onClick={handleClickGoSobre}>
          <h3>Sobre</h3>
        </button>
        <button onClick={handleClickGoContato}>
          <h3>Contato</h3>
        </button>
      </div>
    </div>
  );
}
