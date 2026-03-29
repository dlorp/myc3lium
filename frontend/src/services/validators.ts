/**
 * Runtime validation schemas for WebSocket data.
 *
 * Ensures untrusted WebSocket messages conform to expected shapes
 * before being added to the Zustand store.
 */

import { z } from 'zod';

export const NodeSchema = z.object({
  id: z.string().min(1).max(64),
  type: z.enum(['SPORE', 'HYPHA', 'FROND', 'RHIZOME']),
  callsign: z.string().max(64),
  status: z.enum(['online', 'offline', 'degraded']),
  rssi: z.number().nullable(),
  battery: z.number().min(0).max(100).nullable(),
  last_seen: z.string(),
  position: z
    .object({
      lat: z.number().min(-90).max(90),
      lon: z.number().min(-180).max(180),
    })
    .nullable(),
});

export const ThreadSchema = z.object({
  id: z.string().min(1).max(64),
  source_id: z.string().min(1).max(64),
  target_id: z.string().min(1).max(64),
  radio_type: z.enum(['LoRa', 'HaLow', 'WiFi']),
  rssi: z.number().nullable(),
  quality: z.number().min(0).max(1),
  latency: z.number().nullable(),
  established: z.string(),
});

export const MessageSchema = z.object({
  id: z.string().min(1).max(64),
  sender_id: z.string().min(1).max(64),
  recipient_id: z.string().max(64).nullable(),
  content: z.string().max(1024),
  timestamp: z.string(),
  hops: z.number().min(0),
});

export type ValidatedNode = z.infer<typeof NodeSchema>;
export type ValidatedThread = z.infer<typeof ThreadSchema>;
export type ValidatedMessage = z.infer<typeof MessageSchema>;
