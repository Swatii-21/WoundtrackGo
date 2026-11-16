from pathlib import Path
import base64

import streamlit as st

from ui.common import ss


def _left_artwork() -> str:
    """Read the cropped WoundTrack branding/wound-care artwork."""
    image_path = Path(__file__).resolve().parents[2] / "assets" / "woundtrack_left_panel.png"
    return base64.b64encode(image_path.read_bytes()).decode("ascii")


def login():
    artwork = _left_artwork()

    st.markdown(
        f"""
        <style>
          /* Login-only full-screen layout */
          #MainMenu, header, footer,
          section[data-testid="stSidebar"],
          [data-testid="stToolbar"],
          [data-testid="stDecoration"] {{
            display: none !important;
          }}

          html, body, .stApp,
          [data-testid="stAppViewContainer"],
          [data-testid="stMain"],
          [data-testid="stMainBlockContainer"] {{
            width: 100% !important;
            min-width: 0 !important;
            min-height: 100vh !important;
            margin: 0 !important;
            padding: 0 !important;
          }}

          .stApp {{
            background: #f8fbfc !important;
            overflow-x: hidden !important;
          }}

          .stApp .main .block-container,
          [data-testid="stMainBlockContainer"] {{
            max-width: none !important;
            width: 100% !important;
            padding: 0 !important;
            margin: 0 !important;
          }}

          .st-key-loginwrap {{
            width: 100% !important;
            min-height: 100vh !important;
            height: 100vh !important;
            padding: 0 !important;
            margin: 0 !important;
            border: 0 !important;
            border-radius: 0 !important;
            box-shadow: none !important;
            background: #f8fbfc !important;
            overflow: hidden !important;
          }}

          .st-key-loginwrap > [data-testid="stVerticalBlock"] {{
            height: 100% !important;
            min-height: 100vh !important;
            gap: 0 !important;
          }}

          .st-key-loginwrap [data-testid="stHorizontalBlock"] {{
            min-height: 100vh !important;
            height: 100vh !important;
            gap: 0 !important;
            align-items: stretch !important;
          }}

          .st-key-loginwrap [data-testid="column"] {{
            min-width: 0 !important;
            padding: 0 !important;
          }}

          /* Left side: only the artwork, no duplicate login controls baked into it */
          .st-key-loginwrap [data-testid="column"]:first-child {{
            flex: 0 0 48% !important;
            width: 48% !important;
            max-width: 48% !important;
            background: linear-gradient(145deg,#e9f8f7,#d8f0ed) !important;
            overflow: hidden !important;
          }}

          .st-key-loginwrap .wt-left-art {{
            width: 100%;
            height: 100vh;
            min-height: 100vh;
            background-image: url("data:image/png;base64,{artwork}");
            background-repeat: no-repeat;
            background-position: center center;
            background-size: 100% 100%;
          }}

          /* Right side: clean white panel and real Streamlit form */
          .st-key-loginwrap [data-testid="column"]:last-child {{
            flex: 1 1 52% !important;
            width: 52% !important;
            max-width: 52% !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
            background:
              radial-gradient(circle at 100% 0%, rgba(225,246,243,.45), transparent 35%),
              #ffffff !important;
            padding: 5vh clamp(28px, 5vw, 88px) !important;
            box-sizing: border-box !important;
          }}

          .st-key-loginwrap .wt-login-heading {{
            max-width: 520px;
            width: 100%;
            margin: 0 auto 34px auto;
          }}

          .st-key-loginwrap .wt-login-heading h1 {{
            color: #102f4d;
            font-size: clamp(30px, 3vw, 43px);
            line-height: 1.12;
            font-weight: 800;
            margin: 0 0 9px 0;
            letter-spacing: -1px;
          }}

          .st-key-loginwrap .wt-login-heading p {{
            color: #526b80;
            font-size: clamp(14px, 1.25vw, 17px);
            margin: 0;
          }}

          .st-key-loginwrap [data-testid="stForm"] {{
            max-width: 520px !important;
            width: 100% !important;
            margin: 0 auto !important;
            padding: 0 !important;
            border: 0 !important;
            background: transparent !important;
          }}

          .st-key-loginwrap .stTextInput {{
            margin: 0 0 17px 0 !important;
          }}

          .st-key-loginwrap .stTextInput label,
          .st-key-loginwrap [data-testid="stCheckbox"] label p {{
            display: none !important;
          }}

          .st-key-loginwrap .stTextInput input {{
            box-sizing: border-box !important;
            height: 62px !important;
            min-height: 62px !important;
            width: 100% !important;
            border: 1.5px solid #dbe5ed !important;
            border-radius: 15px !important;
            background: #ffffff !important;
            color: #173650 !important;
            font-size: 17px !important;
            padding: 0 22px !important;
            box-shadow: 0 3px 12px rgba(20,55,78,.055) !important;
            transition: border-color .18s ease, box-shadow .18s ease !important;
          }}

          .st-key-loginwrap .stTextInput input:focus {{
            border-color: #168d83 !important;
            box-shadow: 0 0 0 3px rgba(22,141,131,.10) !important;
          }}

          .st-key-loginwrap .stTextInput input::placeholder {{
            color: #8293a3 !important;
            opacity: 1 !important;
          }}

          .st-key-loginwrap .stFormSubmitButton {{
            margin-top: 6px !important;
          }}

          .st-key-loginwrap .stFormSubmitButton button {{
            height: 62px !important;
            min-height: 62px !important;
            width: 100% !important;
            border: 0 !important;
            border-radius: 15px !important;
            background: linear-gradient(100deg,#087d76,#07877f) !important;
            color: #ffffff !important;
            font-size: 18px !important;
            font-weight: 700 !important;
            box-shadow: 0 7px 18px rgba(0,115,105,.17) !important;
            transition: transform .18s ease, box-shadow .18s ease !important;
          }}

          .st-key-loginwrap .stFormSubmitButton button:hover {{
            background: linear-gradient(100deg,#066e68,#087a73) !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 9px 20px rgba(0,115,105,.20) !important;
          }}

          .st-key-loginwrap [data-testid="stCheckbox"] {{
            margin-top: 15px !important;
          }}

          .st-key-loginwrap [data-testid="stCheckbox"] label {{
            color: #24435c !important;
            font-size: 14px !important;
            font-weight: 600 !important;
          }}

          .st-key-loginwrap [data-testid="stCheckbox"] label p {{
            display: block !important;
          }}

          .st-key-loginwrap [data-testid="stCheckbox"] input {{
            accent-color: #087d76 !important;
          }}

          .st-key-loginwrap .wt-secure {{
            max-width: 520px;
            width: 100%;
            margin: 42px auto 0 auto;
            text-align: center;
            color: #64798b;
            font-size: 13px;
            letter-spacing: .1px;
          }}

          .st-key-loginwrap [data-testid="stAlert"] {{
            max-width: 520px !important;
            margin: 14px auto 0 auto !important;
            border-radius: 12px !important;
          }}

          /* On narrow screens, retain the brand as a compact banner above the form. */
          @media (max-width: 900px) {{
            .st-key-loginwrap,
            .st-key-loginwrap > [data-testid="stVerticalBlock"],
            .st-key-loginwrap [data-testid="stHorizontalBlock"] {{
              height: auto !important;
              min-height: 100vh !important;
            }}

            .st-key-loginwrap [data-testid="stHorizontalBlock"] {{
              flex-direction: column !important;
            }}

            .st-key-loginwrap [data-testid="column"]:first-child {{
              flex: 0 0 auto !important;
              width: 100% !important;
              max-width: 100% !important;
              height: 34vh !important;
              min-height: 230px !important;
            }}

            .st-key-loginwrap .wt-left-art {{
              height: 34vh !important;
              min-height: 230px !important;
              background-size: auto 100% !important;
              background-position: left center !important;
            }}

            .st-key-loginwrap [data-testid="column"]:last-child {{
              flex: 1 1 auto !important;
              width: 100% !important;
              max-width: 100% !important;
              padding: 34px 7vw 38px !important;
            }}

            .st-key-loginwrap .wt-login-heading {{
              margin-bottom: 24px !important;
            }}

            .st-key-loginwrap .wt-secure {{
              margin-top: 26px !important;
            }}
          }}

          @media (max-height: 720px) and (min-width: 901px) {{
            .st-key-loginwrap [data-testid="column"]:last-child {{
              padding-top: 24px !important;
              padding-bottom: 24px !important;
            }}
            .st-key-loginwrap .wt-login-heading {{
              margin-bottom: 20px !important;
            }}
            .st-key-loginwrap .stTextInput input {{
              height: 54px !important;
              min-height: 54px !important;
            }}
            .st-key-loginwrap .stTextInput {{
              margin-bottom: 12px !important;
            }}
            .st-key-loginwrap .stFormSubmitButton button {{
              height: 56px !important;
              min-height: 56px !important;
            }}
            .st-key-loginwrap .wt-secure {{
              margin-top: 22px !important;
            }}
          }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.container(key="loginwrap"):
        left, right = st.columns([0.48, 0.52], gap=None)

        with left:
            st.markdown('<div class="wt-left-art" aria-label="WoundTrack wound care monitoring"></div>',
                        unsafe_allow_html=True)

        with right:
            st.markdown(
                """
                <div class="wt-login-heading">
                  <h1>Doctor Login</h1>
                  <p>Access your patient dashboard</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.form("doctor_login_form", border=False):
                email = st.text_input(
                    "Email address",
                    placeholder="Enter your email",
                    label_visibility="collapsed",
                )
                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter password",
                    label_visibility="collapsed",
                )
                submitted = st.form_submit_button("Sign In  →", use_container_width=True)
                remember = st.checkbox("Remember me", value=False)

            st.markdown(
                '<div class="wt-secure">♢ &nbsp; Secure • Confidential • Trusted</div>',
                unsafe_allow_html=True,
            )

            if submitted:
                if email.strip() and password == "demo123":
                    ss.auth = True
                    st.rerun()
                else:
                    st.error("For demo access, enter an email and password: demo123.")


render = login
