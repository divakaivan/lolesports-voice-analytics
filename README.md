## **Problem Statement**  

In League of Legends esports (LoLEsports), team communication remains private, with practice sessions and in-game voice comms restricted to teams and Riot Games (the game's developer). As a result, teams primarily rely on structured data—such as in-game statistics—to analyze performance, leaving a critical gap in understanding real-time communication and decision-making.

However, team communication is one of the most crucial factors in competitive play. Recent advancements in AI-driven speech analysis now make it possible to extract insights from unstructured audio data, helping teams better understand coordination, shot-calling efficiency, and strategic adaptation. Despite this potential, most teams lack the resources to develop AI-powered tools for audio analysis.

## **Advancing Speech AI for Esports**

While modern speech AI models perform well on conversations with 1-3 speakers, competitive gaming presents a unique challenge due to its fast-paced, multi-speaker environment, with at least five players communicating simultaneously. Current models struggle with overlapping speech, speaker diarization, and noisy environments.

By developing a structured pipeline for audio extraction and analysis, this project also serves as a template for improving speaker diarization models, contributing to the broader advancement of AI in esports communication analysis.

## **Opportunity**

Recently, Los Ratones, a team in the 2nd tier of the Europe, Middle East, and Africa (EMEA) league, has started publicly sharing full in-game voice communications on Twitch and YouTube. This presents a unique opportunity for the open-source community to develop tools that analyze team communication for the first time.

By leveraging these publicly available datasets, we can create AI-powered solutions that help teams, analysts, and fans better understand in-game communication.

## **Key stakeholders**

- **Players & Coaches:** To improve player communication, reduce redundant callouts, and optimize team synergy.  
- **Analysts & Broadcasters:** To generate player/team-specific insights and summaries.  
- **Fans & Content Creators:** To receive more information about their favourite player/team.

---

## **Conceptual Data Model (Technology-Agnostic)**  

The model represents core entities and their relationships:  

```plaintext
[Video] 
   |--< [Team] 
   |        |--< [Player]  
   |  
   |--< [Audio] (Full Game)  
   |        |--< [Player-Specific Audio]  
   |  
   |--< [Text] (Transcription)  
            |--< [Player-Specific Text]  

[Team]  
   |--< [Player]  

[Audio]  
   |--< [Text]  
   |--< [Player]  

[Player]  
   |--< [Game Performance] (KDA, objectives, communication metrics)  
```

### **Key Entity Descriptions:**  
- **Video:** The primary source containing metadata and raw team communication.  
- **Team:** Represents a team participating in the game, linking to players.  
- **Player:** Individual participants whose communication and performance data are analyzed.  
- **Audio:** Extracted from videos, broken into full-game and player-specific segments.  
- **Text:** Transcriptions from audio, linked to players where possible.  
- **Game Performance:** Player statistics to correlate with communication style.  

---

## **Challenges & Data Considerations**  

### **Data Quality & Preprocessing Issues**  
- **Speech-to-Text Accuracy:** Errors in transcriptions due to accents, background noise, or overlapping speech.  
- **Speaker Identification:** Separating individual voices from team communication audio is challenging.  
- **Incomplete Data:** Some videos may have missing team/player info or unclear audio.  

### **Data Volume & API Rate Limits**  
- **YouTube API:** Enforces daily request limits, requiring batching or rate-limiting strategies.  
- **Fandom.com Scraping:** Pages may change in structure, needing robust selectors and monitoring.  
- **Storage & Processing:** Weekly collection of large audio files requires optimized storage and processing pipelines.  

### **Pipeline Frequency**  
- **Weekly automatic ingestion for new games.**  
- **On-demand processing for specific videos.**  

---

## **Success Metrics**  
- **Transcription Accuracy (%)** – Measuring how well speech-to-text models perform.  
- **Speaker Identification Rate (%)** – Accuracy of assigning speech to individual players.  
- **Communication Pattern Insights** – Quantified trends (e.g., average call frequency per minute).  
- **Fan Engagement Metrics** – Views, likes, and shares on auto-generated game summaries.  


