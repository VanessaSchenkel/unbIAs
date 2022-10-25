import copyImg from "../assets/copy.svg";

const TranslationGender = ({ translations, optionNeutral }) => {
  const titles = ["Tradução: ", "Neutro: "];

  const formatNeutral = (translation) => {
    const word = translation.replace("[x]", optionNeutral["label"]);

    return word;
  };

  function copyRoomCodeToClipboard(translation) {
    navigator.clipboard.writeText(translation);
  }

  console.log(Object.keys(translations).map((i) => i));
  return (
    <div className='traducao'>
      <div className='title'>Traduções:</div>
      {Object.values(translations)
        .reverse()
        .map((translation, index) => {
          return (
            <>
              <div className='textarea-container'>
                <div className='title-gender'>{titles[index]}</div>
                <textarea
                  className='translations-textarea'
                  disabled
                  value={formatNeutral(translation)}></textarea>
                <button
                  className='botao-copiar'
                  onClick={() => copyRoomCodeToClipboard(translation)}>
                  <img className='img-copiar' src={copyImg} alt='Copiar' />
                </button>
              </div>
            </>
          );
        })}
    </div>
  );
};

export default TranslationGender;
