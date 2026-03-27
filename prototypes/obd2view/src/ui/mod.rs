// TUI layer - ratatui interface with PSX aesthetic

use crate::config::{Config, Units};
use crate::obd2::OBD2Manager;
use crate::protocol::{Pid, PidValue};
use anyhow::Result;
use crossterm::{
    event::{self, Event, KeyCode, KeyEventKind},
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use ratatui::{
    backend::CrosstermBackend,
    layout::{Alignment, Constraint, Direction, Layout},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, Gauge, Paragraph},
    Terminal,
};
use std::io;
use std::time::Duration;

pub struct App {
    config: Config,
    current_view: View,
}

#[derive(Debug, Clone, Copy)]
enum View {
    Dashboard,
    Dtcs,
    Logger,
    Config,
}

impl App {
    pub fn new(config: Config) -> Result<Self> {
        Ok(Self {
            config,
            current_view: View::Dashboard,
        })
    }

    pub async fn run(&mut self) -> Result<()> {
        // Setup terminal
        enable_raw_mode()?;
        let mut stdout = io::stdout();
        execute!(stdout, EnterAlternateScreen)?;
        let backend = CrosstermBackend::new(stdout);
        let mut terminal = Terminal::new(backend)?;

        // Connect to OBD2
        let mut obd2 = match OBD2Manager::connect(&self.config).await {
            Ok(mgr) => Some(mgr),
            Err(e) => {
                eprintln!("Failed to connect to OBD2: {}", e);
                None
            }
        };

        // Main event loop
        let result = self.run_loop(&mut terminal, &mut obd2).await;

        // Cleanup terminal
        disable_raw_mode()?;
        execute!(terminal.backend_mut(), LeaveAlternateScreen)?;
        terminal.show_cursor()?;

        result
    }

    async fn run_loop(
        &mut self,
        terminal: &mut Terminal<CrosstermBackend<io::Stdout>>,
        obd2: &mut Option<OBD2Manager>,
    ) -> Result<()> {
        let imperial = matches!(self.config.units, Units::Imperial);

        loop {
            // Fetch live data
            let (rpm, speed, temp, load) = if let Some(manager) = obd2.as_mut() {
                let pids = vec![
                    Pid::ENGINE_RPM,
                    Pid::VEHICLE_SPEED,
                    Pid::COOLANT_TEMP,
                    Pid::ENGINE_LOAD,
                ];

                let data = manager.get_pids(&pids).await.unwrap_or_default();

                (
                    data.get(&Pid::ENGINE_RPM).cloned(),
                    data.get(&Pid::VEHICLE_SPEED).cloned(),
                    data.get(&Pid::COOLANT_TEMP).cloned(),
                    data.get(&Pid::ENGINE_LOAD).cloned(),
                )
            } else {
                (None, None, None, None)
            };

            // Render UI
            terminal.draw(|f| {
                let size = f.size();

                // PSX blue theme
                let title_style = Style::default()
                    .fg(Color::Rgb(0, 0, 205)) // PSX blue (#0000CD)
                    .add_modifier(Modifier::BOLD);

                let main_block = Block::default()
                    .title("OBD2VIEW - Diagnostic Monitor")
                    .title_alignment(Alignment::Center)
                    .borders(Borders::ALL)
                    .border_style(title_style);

                let inner = main_block.inner(size);
                f.render_widget(main_block, size);

                // 2x2 grid layout
                let rows = Layout::default()
                    .direction(Direction::Vertical)
                    .constraints([Constraint::Percentage(50), Constraint::Percentage(50)])
                    .split(inner);

                let top_cols = Layout::default()
                    .direction(Direction::Horizontal)
                    .constraints([Constraint::Percentage(50), Constraint::Percentage(50)])
                    .split(rows[0]);

                let bottom_cols = Layout::default()
                    .direction(Direction::Horizontal)
                    .constraints([Constraint::Percentage(50), Constraint::Percentage(50)])
                    .split(rows[1]);

                // Gauges
                render_gauge(f, top_cols[0], "RPM", &rpm, 7000, imperial);
                render_gauge(f, top_cols[1], "SPEED", &speed, 200, imperial);
                render_gauge(f, bottom_cols[0], "TEMP", &temp, 120, imperial);
                render_gauge(f, bottom_cols[1], "LOAD", &load, 100, imperial);

                // Footer
                let footer_area = ratatui::layout::Rect {
                    x: inner.x,
                    y: inner.y + inner.height,
                    width: inner.width,
                    height: 1,
                };

                let footer = Paragraph::new(Line::from(vec![
                    Span::raw("Press "),
                    Span::styled("Q", Style::default().add_modifier(Modifier::BOLD)),
                    Span::raw(" to quit | "),
                    Span::raw(if obd2.is_some() {
                        "● Connected"
                    } else {
                        "○ Disconnected"
                    }),
                ]))
                .alignment(Alignment::Center);
                
                f.render_widget(footer, footer_area);
            })?;

            // Handle input (non-blocking)
            if event::poll(Duration::from_millis(100))? {
                if let Event::Key(key) = event::read()? {
                    if key.kind == KeyEventKind::Press {
                        match key.code {
                            KeyCode::Char('q') | KeyCode::Char('Q') => break,
                            KeyCode::Esc => break,
                            _ => {}
                        }
                    }
                }
            }
        }

        Ok(())
    }
}

fn render_gauge<B: ratatui::backend::Backend>(
    f: &mut ratatui::Frame<B>,
    area: ratatui::layout::Rect,
    label: &str,
    value: &Option<PidValue>,
    max: u16,
    imperial: bool,
) {
    let (display, ratio) = match value {
        Some(PidValue::Rpm(rpm)) => {
            let ratio = (*rpm as f64) / (max as f64);
            (format!("{} rpm", rpm), ratio)
        }
        Some(PidValue::Speed(kmh)) => {
            let ratio = (*kmh as f64) / (max as f64);
            if imperial {
                let mph = (*kmh as f32 * 0.621371) as u8;
                (format!("{} mph", mph), ratio)
            } else {
                (format!("{} km/h", kmh), ratio)
            }
        }
        Some(PidValue::Temperature(celsius)) => {
            let ratio = (*celsius as f64) / (max as f64);
            if imperial {
                let fahrenheit = (*celsius as f32 * 9.0 / 5.0) + 32.0;
                (format!("{:.0}°F", fahrenheit), ratio)
            } else {
                (format!("{}°C", celsius), ratio)
            }
        }
        Some(PidValue::Percentage(pct)) => {
            let ratio = (*pct as f64) / 100.0;
            (format!("{:.1}%", pct), ratio)
        }
        _ => ("--".to_string(), 0.0),
    };

    let gauge_color = if ratio > 0.8 {
        Color::Red // High warning
    } else if ratio > 0.6 {
        Color::Yellow // Medium
    } else {
        Color::Rgb(0, 255, 0) // PSX green (#00FF00)
    };

    let gauge = Gauge::default()
        .block(
            Block::default()
                .title(label)
                .borders(Borders::ALL)
                .border_style(Style::default().fg(Color::Rgb(0, 0, 205))),
        )
        .gauge_style(Style::default().fg(gauge_color))
        .label(display)
        .ratio(ratio.clamp(0.0, 1.0));

    f.render_widget(gauge, area);
}
