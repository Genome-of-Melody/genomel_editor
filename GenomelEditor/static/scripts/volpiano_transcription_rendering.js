
const SYLLABLE_VOLPIANO_DIV_CLASS = 'syllable_volpiano';
const SYLLABLE_TEXT_DIV_CLASS = 'syllable_syllabized_text';
const SYLLABLE_CONTAINER_DIV_CLASS = 'syllable_container';
const WORD_CONTAINER_DIV_CLASS = 'word_container';

const VOLPIANO_WORD_SEPARATOR = '---';
const VOLPIANO_SYLLABLE_SEPARATOR = '--';

const TEXT_WORD_SEPARATOR = '_';
const TEXT_SYLLABLE_SEPARATOR = '-';

const VOLPIANO_EMPTY_SYLLABLE = '-';
const TEXT_EMPTY_SYLLABLE = '...';


// Helper functions that create the proper HTML elements and their ids.

function _create_word_container_id(word_index) {
    return 'word_container_' + word_index;
}

function _create_word_container_div(word_id) {
    const word_div = document.createElement('div');
    word_div.setAttribute('id', word_id);
    word_div.setAttribute('class', WORD_CONTAINER_DIV_CLASS);
    return word_div;
}


function _create_syllable_container_id(word_index, syllable_index) {
    return 'syllable_container_w-' + word_index + '_s-' + syllable_index;
}

function _create_syllable_container_div(syllable_id) {
    const syllable_container_div = document.createElement('div');
    syllable_container_div.setAttribute('id', syllable_id);
    syllable_container_div.setAttribute('class', SYLLABLE_CONTAINER_DIV_CLASS);
    return syllable_container_div;
}


function _create_syllable_volpiano_div_id(word_index, syllable_index) {
    return 'syllable_volpiano_w-' + word_index + '_s-' + syllable_index;
}

function _create_syllable_volpiano_div(syllable_id, volpiano, is_last_syllable_in_word) {
    const syllable_div = document.createElement('div');
    syllable_div.setAttribute('id', syllable_id);
    syllable_div.setAttribute('class', SYLLABLE_VOLPIANO_DIV_CLASS);
    syllable_div.innerHTML = volpiano + VOLPIANO_SYLLABLE_SEPARATOR;
    if (is_last_syllable_in_word) {
        syllable_div.innerHTML = volpiano + VOLPIANO_WORD_SEPARATOR;
    }
    return syllable_div;
}


function _create_syllable_text_div_id(word_index, syllable_index) {
    return 'syllable_text_w-' + word_index + '_s-' + syllable_index;
}

function _create_syllable_text_div(syllable_id, text, is_last_syllable_in_word) {
    const syllable_div = document.createElement('div');
    syllable_div.setAttribute('id', syllable_id);
    syllable_div.setAttribute('class', SYLLABLE_TEXT_DIV_CLASS);
    syllable_div.innerHTML = text + TEXT_SYLLABLE_SEPARATOR;
    if (is_last_syllable_in_word) {
        syllable_div.innerHTML = text + TEXT_WORD_SEPARATOR;
    }
    return syllable_div;
}



function _create_clef_word(clef, rendering_container) {
    const volpiano_clef_header_word_container = _create_word_container_div('volpiano_clef_header_word');
    rendering_container.appendChild(volpiano_clef_header_word_container);
    const volpiano_clef_header_syllable_container = _create_syllable_container_div('volpiano_clef_header_syllable');
    volpiano_clef_header_word_container.appendChild(volpiano_clef_header_syllable_container);

    const volpiano_clef_header_id = 'volpiano_clef_header';
    const volpiano_clef_header_div = _create_syllable_volpiano_div(
        volpiano_clef_header_id, clef, true);
    volpiano_clef_header_syllable_container.appendChild(volpiano_clef_header_div);

    // Add a fake text word with one syllable to maintain vertical alignment.
    const volpiano_clef_header_text_div = _create_syllable_text_div(
        'volpiano_clef_header_text', '...', true);
    volpiano_clef_header_syllable_container.appendChild(volpiano_clef_header_text_div);
}



// Render the volpiano transcription and the syllabized text into the provided container.
function render(volpiano, syllabized_text, rendering_container) {
    // Clear the container.
    rendering_container.innerHTML = '';

    // Split into list of words, then each word into list of syllables.
    // Result is a list of lists of syllables for both volpiano and syllabized text.
    const volpiano_words = volpiano.split('---');
    // console.log('Volpiano words:');
    // console.log(volpiano_words);

    const volpiano_word_syllables = [];
    for (const volpiano_word of volpiano_words) {
        volpiano_word_syllables.push(volpiano_word.split('--'));
    }
    // console.log('Volpiano word syllables:');
    // console.log(volpiano_word_syllables);

    const syllabized_text_words = syllabized_text.split(' ');
    // console.log('Syllabized text words:');
    // console.log(syllabized_text_words);

    const syllabized_text_words_syllables = [];
    for (const syllabized_text_word of syllabized_text_words) {
        syllabized_text_words_syllables.push(syllabized_text_word.split('-'));
    }
    // console.log('Syllabized text word syllables:');
    // console.log(syllabized_text_words_syllables);

    // Render the Volpiano clef header 1--- without eating up a text word:
    let clef = '1'
    // If the Volpiano really starts with a clef, then we have to throw out this word
    // in order to keep the proper alignment between Volpiano and text words.
    if (volpiano_word_syllables[0][0] === '1') {
        clef = volpiano_word_syllables[0][0];
        volpiano_word_syllables.shift(); // Throw out the first word
    }
    _create_clef_word(clef, rendering_container)

    // Render by word and within each word by syllable.
    const n_words_volpiano = volpiano_word_syllables.length;
    const n_words_syllabized_text = syllabized_text_words_syllables.length;
    const n_words = Math.max(n_words_volpiano, n_words_syllabized_text);
    for (let i = 0; i < n_words; i++) {
        // Render the current word.

        // Add a div for the current word.
        const word_div_id = _create_word_container_id(i);
        const word_div = _create_word_container_div(word_div_id);
        rendering_container.appendChild(word_div);

        // If there is no volpiano, just render the text word.
        if (i >= n_words_volpiano) {
            const word_syllabized_text = syllabized_text_words_syllables[i];
            let j = 0; // We only need this for generating the correct id.
            for (const syllable_syllabized_text of word_syllabized_text) {
                // Render the current syllable.
                const syllable_container_div_id = _create_syllable_container_id(i, j);
                const syllable_container_div = _create_syllable_container_div(syllable_container_div_id);
                word_div.appendChild(syllable_container_div);

                const fake_volpiano_div_id = _create_syllable_volpiano_div_id(i, j);
                const fake_volpiano_div = _create_syllable_volpiano_div(fake_volpiano_div_id, '-', j === word_syllabized_text.length - 1);
                syllable_container_div.appendChild(fake_volpiano_div);

                const syllable_text_div_id = _create_syllable_text_div_id(i, j);
                const syllable_text_div = _create_syllable_text_div(
                    syllable_text_div_id,
                    syllable_syllabized_text,
                    j === word_syllabized_text.length - 1);
                syllable_container_div.appendChild(syllable_text_div);
                j += 1;
            }
            continue;
        }

        // If there is no text, just render all the volpiano syllables.
        if (i >= n_words_syllabized_text) {
            const word_volpiano = volpiano_word_syllables[i];
            let j = 0; // We only need this for generating the correct id.
            for (const syllable_volpiano of word_volpiano) {
                // Render the current syllable.
                const syllable_container_div_id = _create_syllable_container_id(i, j);
                const syllable_container_div = _create_syllable_container_div(syllable_container_div_id);
                word_div.appendChild(syllable_container_div);

                const syllable_volpiano_div_id = _create_syllable_volpiano_div_id(i, j);
                const syllable_volpiano_div = _create_syllable_volpiano_div(
                    syllable_volpiano_div_id,
                    syllable_volpiano,
                    j === word_volpiano.length - 1);
                syllable_container_div.appendChild(syllable_volpiano_div);

                const fake_text_div_id = _create_syllable_text_div_id(i, j);
                const fake_text_div = _create_syllable_text_div(fake_text_div_id, '...', j === word_volpiano.length - 1);
                syllable_container_div.appendChild(fake_text_div);

                j += 1;
            }
            continue;
        }

        // If there is both text and volpiano, render both.
        const word_volpiano = volpiano_word_syllables[i];
        const word_syllabized_text = syllabized_text_words_syllables[i];

        const n_syllables_volpiano = word_volpiano.length;
        const n_syllables_syllabized_text = word_syllabized_text.length;
        const n_syllables = Math.max(n_syllables_volpiano, n_syllables_syllabized_text);
        for (let j = 0; j < n_syllables; j++) {
            // Render the current syllable.
            // Container has to be there anyway.
            const syllable_container_div_id = _create_syllable_container_id(i, j);
            const syllable_container_div = _create_syllable_container_div(syllable_container_div_id);
            word_div.appendChild(syllable_container_div);

            let syllable_volpiano = VOLPIANO_EMPTY_SYLLABLE;
            if (j < n_syllables_volpiano) {
                syllable_volpiano = word_volpiano[j];
            }
            const syllable_volpiano_div_id = _create_syllable_volpiano_div_id(i, j);
            const syllable_volpiano_div= _create_syllable_volpiano_div(
                syllable_volpiano_div_id,
                syllable_volpiano,
                j === n_syllables_volpiano - 1);
            syllable_container_div.appendChild(syllable_volpiano_div);

            let syllable_text = TEXT_EMPTY_SYLLABLE;
            if (j < n_syllables_syllabized_text) {
                syllable_text = word_syllabized_text[j];
            }
            console.log('Syllable text: ');
            console.log(syllable_text);
            if (syllable_text === undefined) {
                console.log('Syllable text undefined!');
                console.log('i: ' + i);
                console.log('j: ' + j);
                console.log('n_syllables_syllabized_text: ' + n_syllables_syllabized_text);
                console.log('word_syllabized_text:');
                console.log(word_syllabized_text);
            }
            // Render the text syllable.
            const syllable_text_div_id = _create_syllable_text_div_id(i, j);
            const syllable_text_div = _create_syllable_text_div(
                syllable_text_div_id,
                syllable_text,
                j === n_syllables_syllabized_text - 1);
            syllable_container_div.appendChild(syllable_text_div);
        }
    }
}
