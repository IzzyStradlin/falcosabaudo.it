import cohere
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox

# Inizializzazione dell'API Cohere
co = cohere.ClientV2("BHVtdp8pxKtkUZGtyNGmxjpp0E7KDMX2QI8XYGsv")

# Funzione per inviare la domanda e ottenere la risposta dal modello
def ask_cohere():
    question = question_entry.get("1.0", tk.END).strip()
    if not question:
        messagebox.showwarning("Warning", "Please enter a question.")
        return
    
    try:
        # Chiamata API per inviare la domanda al modello Cohere
        response = co.chat(
            model="command-a-03-2025",
            messages=[{"role": "user", "content": question}]
        )

        # Reset del box di risposta prima di visualizzare la risposta
        response_text.delete("1.0", tk.END)

        # Estrarre e visualizzare la risposta
        answer = response.message.content[0].text.strip()
        if answer:
            print(f"Response: {answer}")
            update_response_text(answer)  # Aggiorna il box di risposta

    except Exception as e:
        messagebox.showerror("Error", f"Error with Cohere API: {e}")
        print(f"Error with Cohere API: {e}")

# Funzione per aggiornare il box di risposta
def update_response_text(answer):
    response_text.insert(tk.END, answer)  # Inserisce la risposta nel box di testo
    response_text.yview(tk.END)  # Scrolla fino alla fine per visualizzare la risposta

# Impostazione della GUI
root = ttk.Window(themename="superhero")
root.title("Ontology RDF Viewer with Cohere Integration")
root.geometry("800x600")

# Etichetta e box per la domanda
question_label = ttk.Label(root, text="Enter your question:", font=("Arial", 12))
question_label.pack(pady=10)

question_entry = tk.Text(root, height=5, width=60)
question_entry.pack(pady=10)

# Bottone per inviare la domanda al modello Cohere
ask_button = ttk.Button(root, text="Ask Cohere", command=ask_cohere)
ask_button.pack(pady=10)

# Etichetta e box per visualizzare la risposta
response_label = ttk.Label(root, text="Cohere's Response:", font=("Arial", 12))
response_label.pack(pady=10)

response_text = tk.Text(root, height=60, width=240)
response_text.pack(pady=10)

# Avvia il loop principale della GUI
root.mainloop()
