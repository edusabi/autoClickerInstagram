"""AutoClicker - interface simples para automação visual.

Use apenas de acordo com os termos do site e com as contas que você controla.
A automação de ações em redes sociais pode gerar limitações na conta.
"""
import threading
import time
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

try:
    import pyautogui
except ImportError:
    pyautogui = None

APP_DIR = Path(__file__).resolve().parent
IMG_SEGUINDO = APP_DIR / "seguindo.jpeg"
IMG_CONFIRMAR = APP_DIR / "confirmar.jpeg"

# Limite deliberadamente conservador. O app não tenta contornar limites da plataforma.
MAX_ACTIONS = 50
DEFAULT_CONFIDENCE = 0.85

class AutoClickerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AutoClicker • Instagram")
        self.root.geometry("720x590")
        self.root.minsize(650, 520)
        self.root.configure(bg="#f4f6fb")
        self.stop_event = threading.Event()
        self.worker = None
        self.count = 0
        self.running = False

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background="#f4f6fb")
        style.configure("TLabel", background="#f4f6fb", foreground="#172033", font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI", 20, "bold"), foreground="#172033")
        style.configure("Sub.TLabel", foreground="#667085", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=9)
        style.configure("Start.TButton", foreground="white", background="#635bff")
        style.map("Start.TButton", background=[("disabled", "#b8b8c8"), ("active", "#5148e5")])

        outer = ttk.Frame(root, padding=24)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="AutoClicker", style="Title.TLabel").pack(anchor="w")
        ttk.Label(outer, text="Automação visual com controles simples", style="Sub.TLabel").pack(anchor="w", pady=(2, 18))

        warning = tk.Frame(outer, bg="#fff4df", highlightbackground="#f0d39a", highlightthickness=1)
        warning.pack(fill="x", pady=(0, 16))
        tk.Label(warning, text="Atenção", bg="#fff4df", fg="#855600", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=12, pady=(10, 2))
        tk.Label(warning, text="Mantenha o navegador aberto na lista correta. A automação pode clicar em itens errados ou provocar restrições da plataforma. Use por sua conta e risco; não há garantia contra bloqueios.", bg="#fff4df", fg="#704b00", justify="left", wraplength=630, font=("Segoe UI", 9)).pack(anchor="w", padx=12, pady=(0, 10))

        settings = ttk.Frame(outer)
        settings.pack(fill="x")
        ttk.Label(settings, text="Limite desta execução (máx. 50):").grid(row=0, column=0, sticky="w", pady=5)
        self.limit_var = tk.IntVar(value=10)
        self.limit_spin = tk.Spinbox(settings, from_=1, to=MAX_ACTIONS, textvariable=self.limit_var, width=8, font=("Segoe UI", 10))
        self.limit_spin.grid(row=0, column=1, sticky="w", padx=(12, 0), pady=5)
        ttk.Label(settings, text="Intervalo entre verificações (segundos):").grid(row=1, column=0, sticky="w", pady=5)
        self.interval_var = tk.DoubleVar(value=2.0)
        self.interval_spin = tk.Spinbox(settings, from_=2.0, to=10.0, increment=0.5, textvariable=self.interval_var, width=8, font=("Segoe UI", 10))
        self.interval_spin.grid(row=1, column=1, sticky="w", padx=(12, 0), pady=5)

        self.status_var = tk.StringVar(value="Pronto para iniciar")
        self.count_var = tk.StringVar(value="0")
        status_card = tk.Frame(outer, bg="white", highlightbackground="#e3e7ef", highlightthickness=1)
        status_card.pack(fill="x", pady=16)
        top = tk.Frame(status_card, bg="white")
        top.pack(fill="x", padx=16, pady=(13, 5))
        tk.Label(top, text="STATUS", bg="white", fg="#667085", font=("Segoe UI", 8, "bold")).pack(side="left")
        tk.Label(top, textvariable=self.count_var, bg="white", fg="#635bff", font=("Segoe UI", 22, "bold")).pack(side="right")
        tk.Label(status_card, textvariable=self.status_var, bg="white", fg="#172033", font=("Segoe UI", 10)).pack(anchor="w", padx=16, pady=(0, 14))

        controls = ttk.Frame(outer)
        controls.pack(fill="x")
        self.start_btn = ttk.Button(controls, text="▶  Iniciar", style="Start.TButton", command=self.start)
        self.start_btn.pack(side="left")
        self.stop_btn = ttk.Button(controls, text="■  Parar", command=self.stop, state="disabled")
        self.stop_btn.pack(side="left", padx=8)
        ttk.Button(controls, text="Limpar registro", command=self.clear_log).pack(side="right")

        ttk.Label(outer, text="Registro de atividade").pack(anchor="w", pady=(17, 6))
        log_frame = ttk.Frame(outer)
        log_frame.pack(fill="both", expand=True)
        self.log_box = tk.Text(log_frame, height=10, wrap="word", bg="#111827", fg="#dbe4f0", insertbackground="white", relief="flat", font=("Consolas", 9), padx=10, pady=8, state="disabled")
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_box.yview)
        self.log_box.configure(yscrollcommand=scrollbar.set)
        self.log_box.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.log("Aplicativo pronto. Verifique se o navegador está na tela correta.")
        self.log("Atalho de emergência do PyAutoGUI: mova o mouse para o canto superior esquerdo.")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def log(self, message):
        stamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{stamp}] {message}\n"
        def append():
            self.log_box.configure(state="normal")
            self.log_box.insert("end", line)
            self.log_box.see("end")
            self.log_box.configure(state="disabled")
        self.root.after(0, append)

    def set_status(self, text):
        self.root.after(0, self.status_var.set, text)

    def set_count(self, count):
        self.root.after(0, self.count_var.set, str(count))

    def start(self):
        if self.running:
            return
        if pyautogui is None:
            messagebox.showerror("Dependência ausente", "Instale as dependências executando INSTALAR.bat ou: pip install -r requirements.txt")
            return
        missing = [str(p.name) for p in (IMG_SEGUINDO, IMG_CONFIRMAR) if not p.exists()]
        if missing:
            messagebox.showerror("Imagens ausentes", "Não encontrei: " + ", ".join(missing) + ". Deixe as imagens na mesma pasta do script.")
            return
        try:
            limit = int(self.limit_var.get())
            interval = float(self.interval_var.get())
            if not 1 <= limit <= MAX_ACTIONS or not 2 <= interval <= 10:
                raise ValueError
        except (ValueError, tk.TclError):
            messagebox.showerror("Configuração inválida", "Use limite entre 1 e 50 e intervalo entre 2 e 10 segundos.")
            return
        if not messagebox.askyesno("Confirme antes de iniciar", "Confirma que o navegador está aberto na lista correta e que entende o risco de restrições da plataforma?"):
            return
        self.stop_event.clear()
        self.count = 0
        self.set_count(0)
        self.running = True
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.limit_spin.configure(state="disabled")
        self.interval_spin.configure(state="disabled")
        self.worker = threading.Thread(target=self.run_automation, args=(limit, interval), daemon=True)
        self.worker.start()

    def stop(self):
        if self.running:
            self.stop_event.set()
            self.set_status("Parando com segurança…")
            self.log("Pedido para parar recebido.")
            self.stop_btn.configure(state="disabled")

    def locate_and_click(self, image_path):
        if self.stop_event.is_set():
            return False
        # Em algumas versões do PyAutoGUI, não encontrar a imagem gera
        # ImageNotFoundException em vez de retornar None. Isso é normal:
        # o fluxo deve continuar para rolar a página e tentar novamente.
        try:
            location = pyautogui.locateCenterOnScreen(
                str(image_path), confidence=DEFAULT_CONFIDENCE, grayscale=True
            )
        except Exception as exc:
            if exc.__class__.__name__ == "ImageNotFoundException":
                return False
            raise
        if location is None or self.stop_event.is_set():
            return False
        pyautogui.moveTo(location.x, location.y, duration=0.15)
        if self.stop_event.wait(0.15):
            return False
        pyautogui.click()
        return True

    def run_automation(self, limit, interval):
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.15
        self.log(f"Execução iniciada. Limite configurado: {limit} ação(ões).")
        self.set_status("Preparando navegador… a janela será minimizada")
        # Minimize the GUI rather than closing it: closing would terminate the app.
        # This lets the previously open browser become the foreground window.
        self.root.after(350, self.root.iconify)
        try:
            # Give Windows time to activate the browser before searching the screen.
            if self.stop_event.wait(1.5):
                return
            while self.count < limit and not self.stop_event.is_set():
                try:
                    clicked = self.locate_and_click(IMG_SEGUINDO)
                except Exception as exc:
                    self.log(f"Não foi possível verificar o botão 'Seguindo': {exc}")
                    break
                if clicked:
                    self.log("Botão 'Seguindo' clicado; aguardando confirmação visual.")
                    if self.stop_event.wait(0.8):
                        break
                    try:
                        confirmed = self.locate_and_click(IMG_CONFIRMAR)
                    except Exception as exc:
                        self.log(f"Erro ao procurar confirmação: {exc}")
                        break
                    if confirmed:
                        self.count += 1
                        self.set_count(self.count)
                        self.log(f"Ação confirmada pelo clique. Contagem: {self.count}/{limit}.")
                    else:
                        self.log("Botão de confirmação não encontrado. Nenhuma ação contabilizada.")
                else:
                    # Se não houver botão visível, desce a lista para procurar outros.
                    self.log("Nenhum botão 'Seguindo' visível. Rolando a página para procurar mais...")
                    try:
                        width, height = pyautogui.size()
                        pyautogui.moveTo(width // 2, int(height * 0.70), duration=0.1)
                        pyautogui.scroll(-75)
                        # Aguarda a lista carregar/renderizar após a rolagem antes de procurar de novo.
                        if self.stop_event.wait(0.8):
                            break
                        self.log("Rolagem concluída; procurando novamente por 'Seguindo'.")
                    except Exception as exc:
                        self.log(f"Erro ao rolar a página: {exc}")
                        break
                if self.stop_event.wait(interval):
                    break
            if self.count >= limit:
                self.log("Limite configurado atingido. Execução encerrada.")
                self.set_status("Limite atingido")
            elif self.stop_event.is_set():
                self.log("Execução interrompida pelo usuário.")
                self.set_status("Interrompido pelo usuário")
            else:
                self.set_status("Execução encerrada; confira o registro")
        except pyautogui.FailSafeException:
            self.log("Parada de emergência: mouse movido para o canto superior esquerdo.")
            self.set_status("Parada de emergência ativada")
        except Exception as exc:
            self.log(f"Erro inesperado: {exc}")
            self.set_status("Erro — consulte o registro")
        finally:
            self.root.after(0, self.finish)

    def finish(self):
        self.running = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.limit_spin.configure(state="normal")
        self.interval_spin.configure(state="normal")
        if self.status_var.get() in ("Pronto para iniciar", "Parando com segurança…"):
            self.status_var.set("Execução encerrada")

    def clear_log(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    def on_close(self):
        if self.running:
            self.stop_event.set()
            self.root.after(250, self.root.destroy)
        else:
            self.root.destroy()


def main():
    root = tk.Tk()
    AutoClickerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
