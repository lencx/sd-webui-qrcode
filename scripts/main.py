import os
import io
import base64
import qrcode
import gradio as gr

from modules import script_callbacks, generation_parameters_copypaste, extensions
from modules.shared import opts
from qrcode.image.styledpil import StyledPilImage
from PIL import Image

controlnet_active = "sd-webui-controlnet" in [item.name for item in extensions.active()]

def dot_style(style):
    if style == "Square":
        return qrcode.image.styles.moduledrawers.pil.SquareModuleDrawer()
    elif style == "Gapped Square":
        return qrcode.image.styles.moduledrawers.pil.GappedSquareModuleDrawer()
    elif style == "Circle":
        return qrcode.image.styles.moduledrawers.pil.CircleModuleDrawer()
    elif style == "Rounded":
        return qrcode.image.styles.moduledrawers.pil.RoundedModuleDrawer()
    elif style == "Circle Zebra":
        return qrcode.image.styles.moduledrawers.pil.HorizontalBarsDrawer()
    elif style == "Circle Zebra Vertical":
        return qrcode.image.styles.moduledrawers.pil.VerticalBarsDrawer()

def error_correction_level(level):
    if level == "L":
        return qrcode.constants.ERROR_CORRECT_L
    elif level == "M":
        return qrcode.constants.ERROR_CORRECT_M
    elif level == "Q":
        return qrcode.constants.ERROR_CORRECT_Q
    elif level == "H":
        return qrcode.constants.ERROR_CORRECT_H

def generate_qrcode(text, version, box_size, border, error_correction, qr_dot_style):
    qr = qrcode.QRCode(
        version=version,
        error_correction=error_correction_level(error_correction),
        border=border,
        box_size=box_size,
    )
    qr.add_data(text)
    qr.make(fit=True)
    qrcode_make = qr.make_image(
        fill='black',
        back_color='white',
        module_drawer=dot_style(qr_dot_style),
        image_factory=StyledPilImage,
    )
    out = io.BytesIO()
    qrcode_make.save(out, format='PNG')
    img = Image.open(out)

    return img

def image_to_base64(img_path):
    with open(img_path, "rb") as img_file:
        return "data:image/png;base64," + base64.b64encode(img_file.read()).decode('utf-8')

def on_ui_tabs():
    with gr.Blocks(analytics_enabled=False) as ui:
        with gr.Row():
            with gr.Column():
                qr_text = gr.inputs.Textbox(lines=4, placeholder="Plain text or URL")
                generate_button = gr.Button("Generate", variant="primary")
                with gr.Tab("QR Code Parameter"):
                    qr_version = gr.Slider(label="QR Version (version)", minimum=1, maximum=40, value=8, step=1)
                    qr_box_size = gr.Slider(label="QR Box Size (box_size)", minimum=1, maximum=100, value=12, step=1)
                    qr_border = gr.Slider(label="QR Border", minimum=0, maximum=100, value=4, step=1)
                qr_dot_style = gr.Radio(label="QR Code Styled", choices=["Square", "Gapped Square", "Circle", "Rounded", "Circle Zebra", "Circle Zebra Vertical"], value="Square")
                with gr.Row():
                    qr_error_correction = gr.Radio(label="QR Code Error Correction Level", choices=["L", "M", "Q", "H"], value="H")
                with gr.Accordion("QR Code Helper", open=False):
                    gr.Markdown("""
                        ### QR Code Parameter

                        - **Version**: The version of a QR code determines its size, i.e., the number of rows and columns. The version varies from 1 to 40, and each increment in the version results in an increase of 4 in the size of the QR code.
                        - **Box Size**: This is the pixel size of an individual QR code unit when generating the QR code image.
                        - **Border**: This is the width of the blank area around the QR code image, expressed in the number of QR code units.
                        - The size of the QR code image is **(17 + 4 * version) * box_size** pixels.
                    """)
                    gr.Markdown("---")
                    gr.Markdown(f"""
                        ### QR Code Styled

                        |Label|Styled|Label|Styled|
                        |--|--|--|--|
                        |Square|![]({image_to_base64(os.path.join(os.path.dirname(__file__), "assets/square.png"))})|Gapped Square|![]({image_to_base64(os.path.join(os.path.dirname(__file__), "assets/gapped-square.png"))})|
                        |Circle|![]({image_to_base64(os.path.join(os.path.dirname(__file__), "assets/circle.png"))})|Rounded|![]({image_to_base64(os.path.join(os.path.dirname(__file__), "assets/rounded.png"))})|
                        |Circle Zebra|![]({image_to_base64(os.path.join(os.path.dirname(__file__), "assets/circle-zebra.png"))})|Circle Zebra Vertical|![]({image_to_base64(os.path.join(os.path.dirname(__file__), "assets/circle-zebra-vertical.png"))})|
                    """, elem_classes="dot-style-table")
                    gr.Markdown("---")
                    gr.Markdown("""
                        ### QR Code Error Correction Level

                        - **L**: About 7% or less errors can be corrected.
                        - **M**: About 15% or less errors can be corrected.
                        - **Q**: About 25% or less errors can be corrected.
                        - **H** (default): About 30% or less errors can be corrected.
                    """)
            with gr.Column():
                output = gr.Image(type="pil", elem_id="qrcode_output", interactive=False, show_label=False).style(height=480)
                with gr.Row():
                    send_to_buttons = generation_parameters_copypaste.create_buttons(["img2img", "inpaint", "extras"])
                    for tabname, button in send_to_buttons.items():
                        generation_parameters_copypaste.register_paste_params_button(generation_parameters_copypaste.ParamBinding(paste_button=button, tabname=tabname, source_image_component=output))
                with gr.Row(visible=controlnet_active):
                    send_controlnet_txt2img = gr.Button("Send to ControlNet (txt2img)")
                    send_controlnet_img2img = gr.Button("Send to ControlNet (img2img)")
                    control_net_max_models_num = opts.data.get('control_net_max_models_num', 1)
                    send_controlnet_num = gr.Dropdown([str(i) for i in range(control_net_max_models_num)], label="ControlNet Unit", value="0", interactive=True, visible=(control_net_max_models_num > 1))
                    send_controlnet_txt2img.click(None, [output, send_controlnet_num], None, _js="(i, n) => {sendToControlNet(i, 'txt2img', n)}", show_progress=False)
                    send_controlnet_img2img.click(None, [output, send_controlnet_num], None, _js="(i, n) => {sendToControlNet(i, 'img2img', n)}", show_progress=False)

            generate_button.click(
                fn=generate_qrcode,
                inputs=[qr_text, qr_version, qr_box_size, qr_border, qr_error_correction, qr_dot_style],
                outputs=[output],
            )
        return [(ui, "QR Code", "lencx_qrcode_tab")]

script_callbacks.on_ui_tabs(on_ui_tabs)