import copyImg from "../assets/copy.svg";

const PossibleWords = ({ translations, optionNeutral }) => {
  const titles = ["Masculino: ", "Feminino: ", "Neutro: "];

  const formatNeutral = (translation) => {
    const word = translation.replace("[x]", optionNeutral["label"]);

    return word;
  };

  function copyRoomCodeToClipboard(translation) {
    navigator.clipboard.writeText(translation);
  }

  console.log(translations["possible_words"].map((i) => i));
  return (
    <div className='traducao'>
      <div className='title'>Possíveis traduções:</div>
      {translations["possible_words"].map((translation, index) => {
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

export default PossibleWords;
