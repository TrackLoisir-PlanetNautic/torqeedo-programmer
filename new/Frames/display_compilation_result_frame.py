from tkinter.ttk import Label, Frame
from torqeedo_programmer import TorqeedoProgrammer
from compilation_result import CompilationResult


def render_display_compilation_result_frame(
    right_column_frame: Frame,
    torqeedo_programmer: TorqeedoProgrammer,
):

    show_error_label = Label(right_column_frame, text="Error: ")
    show_error_label.pack(padx=10, pady=10)

    def restart_esp_and_get_infos_status():
        if torqeedo_programmer.selected_controller is None:
            show_error_label.config(text="Error: No controller selected")
        elif torqeedo_programmer.selected_controller.esp_rom is None:
            show_error_label.config(
                text="Error: Please connect to the controller"
            )
        elif (
            torqeedo_programmer.selected_controller.compilation_result
            is None
        ):
            show_error_label.config(
                text="Error: No compilation result, restart esp"
            )

        right_column_frame.after(
            100, restart_esp_and_get_infos_status
        )  # Check every 100ms

    restart_esp_and_get_infos_status()
