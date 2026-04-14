import os
import azure.cognitiveservices.speech as speechsdk

def generate_azure_narration(text, output_path, api_key, region, voice_name="en-US-AvaNeural", speed=1.0):
    """
    Generates narration using Azure Cognitive Services (Speech).
    """
    speech_config = speechsdk.SpeechConfig(subscription=api_key, region=region)
    # Set the voice name
    speech_config.speech_synthesis_voice_name = voice_name
    
    # Configure output format
    audio_config = speechsdk.audio.AudioOutputConfig(filename=output_path)
    
    # Create synthesizer
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    
    # Prosody for speed control
    ssml = f"""
    <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'>
        <voice name='{voice_name}'>
            <prosody rate='{speed}'>
                {text}
            </prosody>
        </voice>
    </speak>"""
    
    result = synthesizer.speak_ssml_async(ssml).get()
    
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        return output_path
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        error_msg = f"Azure Synthesis failed: {cancellation_details.reason}"
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            error_msg += f" (Error details: {cancellation_details.error_details})"
        raise Exception(error_msg)
    
    return None
