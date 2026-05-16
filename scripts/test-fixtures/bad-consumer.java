package com.example.surgery;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.core.KafkaTemplate;

// Test fixture: intentionally bad — Layer 1 validator should flag many issues.
public class BadConsumer {

    // VIOLATION: @Autowired on a field (should be constructor injection).
    @Autowired
    private KafkaTemplate<String, String> kafkaTemplate;

    // VIOLATION: hardcoded config values.
    int batchSize = 100;
    int timeoutMs = 5000;
    int concurrency = 15;

    // VIOLATION: hardcoded Kafka topic literal in @KafkaListener.
    @KafkaListener(topics = "surgery.file.processed", containerFactory = "batchFactory")
    public void onMessages(List<ConsumerRecord<String, String>> messages, Acknowledgment ack) {
        // VIOLATION: offset commit appears BEFORE the processing loop (data-loss risk).
        consumer.commitSync();

        // VIOLATION: per-message loop in batch-mode consumer.
        for (ConsumerRecord<String, String> msg : messages) {
            // VIOLATION: inline MQTT topic construction via string concat.
            String topic = "topic/01/" + msg.key() + "/up/heartbeat";
            // VIOLATION: unregistered MQTT type 'unknownType'.
            String otherTopic = "topic/01/abc/up/unknownType";
            mqttClient.publish(topic, msg.value());
            mqttClient.publish(otherTopic, msg.value());

            // VIOLATION: workflow state literal not present in workflow.md.
            if (status.equals("REJECTED")) {
                status = "ARCHIVED_FOREVER";
            }
        }

        // No DLQ branch anywhere -> VIOLATION: kafka-dlq-required.
    }
}
