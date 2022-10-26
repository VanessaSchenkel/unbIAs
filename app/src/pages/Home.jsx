import { useEffect } from "react";
import { useState } from "react";
import PacmanLoader from "react-spinners/PacmanLoader";
import Select from "react-select";
import PossibleWords from "../components/PossibleWords";
import TranslationGender from "../components/TranslationGender";
import "../styles/home.css";
import { Error } from "./Error";

export function Home() {
  const [newTextToTranslate, setNewTextToTranslate] = useState("");
  const [newTranslation, setNewTranslation] = useState("");
  const [shouldShowPossibleWords, setShouldShowPossibleWords] = useState(false);
  const [shouldShowTranslation, setShouldShowTranslation] = useState(false);
  const [shouldShowError, setShouldShowError] = useState(false);
  const [spinner, setSpinner] = useState(false);
  const [optionNeutral, setOptionNeutral] = useState({
    value: "x",
    label: "[X]",
  });

  const options = [
    { value: "x", label: "[X]" },
    { value: "e", label: "e" },
    { value: "u", label: "u" },
    { value: "at", label: "@" },
  ];

  const handleSendQuestion = (event) => {
    event.preventDefault();
    setSpinner(true);

    // setNewTranslation({ possible_words: ["Cão", "Cadela", "Cã[x]"] });

    if (newTextToTranslate.trim().length > 0) {
      const requestOptions = {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source_sentence: newTextToTranslate }),
      };

      fetch("/translate", requestOptions)
        .then((response) => response.json())
        .then((data) => setNewTranslation(data))
        .then((data) => setSpinner(false))
        .catch((err) => {
          console.log(err);
          setShouldShowError(true);
        });
    }
  };

  useEffect(() => {
    console.log("NEW TRANSLATION:", newTranslation);
    if (newTranslation) {
      const translation = newTranslation;
      if (translation.hasOwnProperty("error")) {
        setShouldShowError(true);
        setShouldShowTranslation(false);
        setShouldShowPossibleWords(false);
      } else if (translation.hasOwnProperty("possible_words")) {
        console.log("entrou possible words");
        setShouldShowError(false);
        setShouldShowTranslation(false);
        setShouldShowPossibleWords(true);
      } else {
        console.log("entrou else");
        setShouldShowError(false);
        setShouldShowPossibleWords(false);
        setShouldShowTranslation(true);
      }
    }
  }, [newTranslation]);

  return (
    <>
      <div id='home'>
        <div className='to-translate'>
          {shouldShowError && <Error />}
          <div className='title'>Texto para traduzir:</div>
          <form onSubmit={handleSendQuestion}>
            <textarea
              className='translate-textarea'
              placeholder='Escreva seu texto para tradução'
              onChange={(event) => setNewTextToTranslate(event.target.value)}
              value={newTextToTranslate}></textarea>
            <div className='select-neutral'>
              <label>Escolha como as traduções neutras devem terminar: </label>
              <Select
                options={options}
                defaultValue={options[0]}
                onChange={(option) => setOptionNeutral(option)}
              />
            </div>
            <button
              className='botao-traduzir'
              type='submit'
              disabled={newTextToTranslate.trim().length === 0}>
              Traduzir
            </button>
          </form>
        </div>
        {shouldShowPossibleWords && (
          <PossibleWords
            translations={newTranslation}
            optionNeutral={optionNeutral}
          />
        )}
        {shouldShowTranslation && (
          <TranslationGender
            translations={newTranslation}
            optionNeutral={optionNeutral}
          />
        )}
      </div>
      {spinner && (
        <div className='loader'>
          <PacmanLoader color='#E83F6F' margin={10} size={50} />
          <h2 className='h2-carregando'>Carregando...</h2>
        </div>
      )}
    </>
  );
}
