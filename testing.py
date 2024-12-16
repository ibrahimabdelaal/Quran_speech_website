import jiwer 
def highlight_alignment(true_text, recognized_text):
    """
    Use jiwer alignment to highlight differences between true and recognized texts.
    """
    print("Highlighting text with alignment...")

    # Process the words to get alignment chunks
    alignment_result = jiwer.process_words(true_text, recognized_text)
    alignment_chunks = alignment_result.alignments
    print("Alignment chunks:", alignment_chunks)
    alignment_chunks=alignment_chunks[0]

    # Flatten the alignment chunks if necessary
    # if isinstance(alignment_chunks, list):
    #     alignment_chunks = [chunk for sublist in alignment_chunks for chunk in sublist]

    highlighted_words = []

    # Iterate over alignment chunks and format based on type
    for chunk in alignment_chunks:
        print(f"Processing chunk: {chunk}")  # Print the current chunk being processed
        if chunk.type == 'equal':
            highlighted_word = f"<span class='highlightright'>{true_text[chunk.ref_start_idx:chunk.ref_end_idx]}</span>"
            highlighted_words.append(highlighted_word)
            print(true_text[0])
            print(true_text[0][0:5])
            print(f"Equal chunk highlighted: {highlighted_word}")  # Print the highlighted word for equal chunks
        elif chunk.type == 'substitute':
            highlighted_word = f"<span class='highlightWrong'>{true_text[chunk.ref_start_idx:chunk.ref_end_idx]}</span>"
            highlighted_words.append(highlighted_word)
            print(f"Substituted chunk highlighted: {highlighted_word}")  # Print the highlighted word for substituted chunks
        elif chunk.type == 'delete':
            highlighted_word = f"<span class='highlighdeleted'>{true_text[chunk.ref_start_idx:chunk.ref_end_idx]}</span>"
            highlighted_words.append(highlighted_word,)
            print(f"Deleted chunk highlighted: {highlighted_word}",true_text[chunk.ref_start_idx:chunk.ref_end_idx])  # Print the highlighted word for deleted chunks
        elif chunk.type == 'insert':
            highlighted_word = f"<span class='highlightInserted'>{true_text[chunk.ref_start_idx:chunk.ref_end_idx]}</span>"
            highlighted_words.append(highlighted_word)
            print(f"Inserted chunk highlighted: {highlighted_word}")  # Print the highlighted word for inserted chunks

    # Join highlighted words into a single string
    aligned_text = ' '.join(highlighted_words)
    print(f"Final aligned text: {aligned_text}")  # Print the final aligned text
    
    return aligned_text

highlight_alignment(['بِسْ مِلْ لَاْ ھِرْ رَحْ مَاْ نِرْ رَ حِيْمْ'], ['بِسْ مِلْ لَاْ ھِرْ رَحْ مَاْنْ'])