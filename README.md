<!-- Images inside <picture> are not turned into links by GitHub; only <a> elements are clickable. -->

<p align="center">
  <picture><img src="assets/header.svg" width="100%"
       alt="Hello World!! I'm Jhojan Espinoza, Mechatronics Engineering student at UNI. A PID line-follower robot follows a crimson track while its left and right PWM values update live." /></picture>
</p>

<p align="center">
  <b>Mechatronics Engineering student at UNI · Embedded firmware for competitive robots</b>
</p>

<p align="center">
  <a href="https://jhojaneco.github.io/JhojanECO/sim/"><img src="https://img.shields.io/badge/Live_demo-PID_lab-DC143C?style=flat-square&logo=githubpages&logoColor=white" alt="Live demo: PID lab" /></a>
  <picture><img src="https://visitor-badge.laobi.icu/badge?page_id=JhojanECO.JhojanECO&left_text=Profile%20views&left_color=%23161B22&right_color=%23DC143C" alt="Profile views" /></picture>
  <!-- TODO: completar y descomentar
  <a href="https://www.linkedin.com/in/TU_LINKEDIN/"><img src="https://img.shields.io/badge/LinkedIn-0A66C2?style=flat-square&logo=linkedin&logoColor=white" alt="LinkedIn" /></a>
  <a href="mailto:TU_CORREO"><img src="https://img.shields.io/badge/Email-161B22?style=flat-square&logo=gmail&logoColor=00F0FF" alt="Email" /></a>
  -->
</p>

<picture><img src="assets/divider.svg" width="100%" alt="" /></picture>

## About me

I write the firmware that makes competition robots move: line followers, mini-sumo and robot soccer. Most of my work runs on bare-metal **ATmega328P**, **ESP32** and **STM32**, where I care about tight control loops, clean timer configuration and code that is modular enough to reuse from one robot to the next.

- **Now:** a line follower with bare-metal timers, PD control, BTN9960LV H-bridges and a brushless suction fan.
- **Learning:** control theory beyond PID, to tune robots by model instead of by trial and error.
- **Open to:** collaborating on embedded systems, robotics and control projects.

## Featured projects

<table>
  <tr>
    <td width="50%" valign="top">
      <a href="https://github.com/JhojanECO/Minisumo-Autonomo-Senior-activacionBT"><b>Mini-Sumo · Senior</b></a><br>
      <sub>Autonomous mini-sumo with Bluetooth start. PID control ported from Arduino to ESP32, with separate modules for sensors, motors, status LED and fight strategy.</sub><br>
      <sub><code>C++</code> <code>ESP32</code> <code>PlatformIO</code></sub>
    </td>
    <td width="50%" valign="top">
      <a href="https://github.com/JhojanECO/SOCCER_SENIOR_PERUHUB_Aldair"><b>Robot Soccer · PERUHUB Senior</b></a><br>
      <sub>Firmware for a senior-category soccer robot driven with a PS5 controller over classic Bluetooth, built for the PERUHUB competition.</sub><br>
      <sub><code>C++</code> <code>ESP32</code> <code>Bluetooth</code></sub>
    </td>
  </tr>
  <tr>
    <td width="50%" valign="top">
      <a href="https://github.com/JhojanECO/esp32_soccer_amateur"><b>Robot Soccer · Amateur</b></a><br>
      <sub>Bluetooth-controlled ESP32 soccer robot, with a step-by-step guide so new team members can build and flash it.</sub><br>
      <sub><code>C++</code> <code>ESP32</code> <code>PlatformIO</code></sub>
    </td>
    <td width="50%" valign="top">
      <a href="https://github.com/JhojanECO/Frecuency_all_timers"><b>High-frequency PWM · ATmega328P</b></a><br>
      <sub>Configures Timer0, Timer1 and Timer2 for fast PWM with a small API to set each channel's duty cycle directly.</sub><br>
      <sub><code>C++</code> <code>ATmega328P</code> <code>Bare-metal</code></sub>
    </td>
  </tr>
</table>

## Interactive PID lab

A browser simulation of my line follower. Change Kp, Ki, Kd and base PWM and watch the robot hold the track or lose it, the same way I tune the real one.

<p align="center">
  <a href="https://jhojaneco.github.io/JhojanECO/sim/">
    <img src="https://img.shields.io/badge/Tune_my_line_follower-DC143C?style=for-the-badge&logo=githubpages&logoColor=00F0FF" alt="Tune my line follower: interactive PID lab" />
  </a>
</p>

## Tech stack

<table>
  <tr>
    <td><b>Languages</b></td>
    <td><picture><img src="https://skillicons.dev/icons?i=cpp,c,py&theme=dark" height="40" alt="C++, C, Python" /></picture></td>
  </tr>
  <tr>
    <td><b>Microcontrollers</b></td>
    <td>
      <picture><img src="https://img.shields.io/badge/ATmega328P-161B22?style=for-the-badge&logo=arduino&logoColor=00F0FF" alt="ATmega328P" /></picture>
      <picture><img src="https://img.shields.io/badge/ESP32-161B22?style=for-the-badge&logo=espressif&logoColor=00F0FF" alt="ESP32" /></picture>
      <picture><img src="https://img.shields.io/badge/STM32-161B22?style=for-the-badge&logo=stmicroelectronics&logoColor=00F0FF" alt="STM32" /></picture>
    </td>
  </tr>
  <tr>
    <td><b>Tools</b></td>
    <td>
      <picture><img src="https://skillicons.dev/icons?i=arduino,git,github,vscode,obsidian&theme=dark" height="40" alt="Arduino, Git, GitHub, VS Code, Obsidian" /></picture>
      <picture><img src="https://img.shields.io/badge/PlatformIO-161B22?style=for-the-badge&logo=platformio&logoColor=00F0FF" alt="PlatformIO" /></picture>
    </td>
  </tr>
</table>

## GitHub activity

<p align="center">
  <picture><img src="assets/stats.svg" width="100%" alt="GitHub activity over the last 12 months and top languages. Refreshed daily by a GitHub Action." /></picture>
</p>

<p align="center">
  <picture><img src="assets/dragon-contrib.svg" width="100%"
       alt="Contribution calendar for the last 12 months. Soplón the dragon leaves his nest, eats the days from the fewest contributions to the most, flies home, and the calendar grows back." /></picture>
</p>
