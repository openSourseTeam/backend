
import os
os.environ["NLTK_DATA"] = "./nltk_data"

import textstat

test_data = (
    "Playing games has always been thought to be important to "
    "the development of well-balanced and creative children; "
    "however, what part, if any, they should play in the lives "
    "of adults has never been researched that deeply. I believe "
    "that playing games is every bit as important for adults "
    "as for children. Not only is taking time out to play games "
    "with our children and other adults valuable to building "
    "interpersonal relationships but is also a wonderful way "
    "to release built up tension."
)

def get_readability(markdown_content):
    readability_scores = {
        'flesch_reading_ease': textstat.flesch_reading_ease(markdown_content),
        'flesch_kincaid_grade': textstat.flesch_kincaid_grade(markdown_content),
        'smog_index': textstat.smog_index(markdown_content),
        'coleman_liau_index': textstat.coleman_liau_index(markdown_content),
        'automated_readability_index': textstat.automated_readability_index(markdown_content),
        'dale_chall_readability_score': textstat.dale_chall_readability_score(markdown_content),
        'difficult_words': textstat.difficult_words(markdown_content),
        'linsear_write_formula': textstat.linsear_write_formula(markdown_content),
        'gunning_fog': textstat.gunning_fog(markdown_content),
        'text_standard': textstat.text_standard(markdown_content),
        'fernandez_huerta': textstat.fernandez_huerta(markdown_content),
        'szigriszt_pazos': textstat.szigriszt_pazos(markdown_content),
        'gutierrez_polini': textstat.gutierrez_polini(markdown_content),
        'crawford': textstat.crawford(markdown_content),
        'gulpease_index': textstat.gulpease_index(markdown_content),
        'osman': textstat.osman(markdown_content)
    }
    return readability_scores



if __name__ == "__main__":
    # nltk.download('cmudict')
    # nltk.data.find("corpora/cmudict")
    print(f'flesch_reading_ease: {textstat.flesch_reading_ease(test_data)}')
    print(f'flesch_kincaid_grade: {textstat.flesch_kincaid_grade(test_data)}')
    print(f'smog_index: {textstat.smog_index(test_data)}')
    print(f'coleman_liau_index: {textstat.coleman_liau_index(test_data)}')
    print(f'automated_readability_index: {textstat.automated_readability_index(test_data)}')
    print(f'dale_chall_readability_score: {textstat.dale_chall_readability_score(test_data)}')
    print(f'difficult_words: {textstat.difficult_words(test_data)}')
    print(f'linsear_write_formula: {textstat.linsear_write_formula(test_data)}')
    print(f'gunning_fog: {textstat.gunning_fog(test_data)}')
    print(f'text_standard: {textstat.text_standard(test_data)}')
    print(f'fernandez_huerta: {textstat.fernandez_huerta(test_data)}')
    print(f'szigriszt_pazos: {textstat.szigriszt_pazos(test_data)}')
    print(f'gutierrez_polini: {textstat.gutierrez_polini(test_data)}')
    print(f'crawford: {textstat.crawford(test_data)}')
    print(f'gulpease_index: {textstat.gulpease_index(test_data)}')
    print(f'osman: {textstat.osman(test_data)}')