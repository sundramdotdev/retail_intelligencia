export interface StoreDTO {
  id?: string;
  storeCode: string;
  name: string;
  address?: string;
  city?: string;
  state?: string;
  postalCode?: string;
  country?: string;
  timezone?: string;
  operatingHours?: any;
  createdAt?: Date;
  updatedAt?: Date;
}

export interface DeviceDTO {
  id?: string;
  deviceId: string;
  storeId: string;
  hardwareModel?: string;
  macAddress?: string;
  status?: string;
  firmwareVersion?: string;
  runtimeVersion?: string;
  lastHeartbeatAt?: Date;
  certificateThumbprint?: string;
  createdAt?: Date;
  updatedAt?: Date;
}

export interface CameraDTO {
  id?: string;
  cameraId: string;
  deviceId: string;
  storeId: string;
  streamType?: string;
  streamUrl?: string;
  resolutionWidth?: number;
  resolutionHeight?: number;
  configuredFps?: number;
  mountLocation?: string;
  status?: string;
  createdAt?: Date;
  updatedAt?: Date;
}

export interface ZoneDTO {
  id?: string;
  zoneCode: string;
  storeId: string;
  cameraId?: string;
  name: string;
  zoneType: string;
  polygonCoordinates: any;
  thresholds?: any;
  isActive?: boolean;
  createdAt?: Date;
  updatedAt?: Date;
}

export interface RetailEventDTO {
  id?: string;
  eventId: string;
  eventVersion: string;
  eventType: string;
  deviceId: string;
  storeId: string;
  zoneId?: string;
  timestamp: Date | string;
  confidence: number;
  severity: string;
  metadata: any;
  source: any;
  schemaVersion?: string;
  receivedAt?: Date;
}

export interface AlertDTO {
  id?: string;
  alertCode: string;
  eventId: string;
  storeId: string;
  zoneId?: string;
  alertType: string;
  severity: string;
  status?: string;
  title: string;
  message: string;
  acknowledgedByUserId?: string;
  acknowledgedAt?: Date;
  resolvedAt?: Date;
  createdAt?: Date;
  updatedAt?: Date;
}

export interface TaskDTO {
  id?: string;
  taskCode: string;
  storeId: string;
  zoneId?: string;
  alertId?: string;
  title: string;
  description?: string;
  priority?: string;
  status?: string;
  assignedToUserId?: string;
  assignedAt?: Date;
  completedAt?: Date;
  resolutionNotes?: string;
  createdAt?: Date;
  updatedAt?: Date;
}

export interface UserDTO {
  id?: string;
  email: string;
  passwordHash: string;
  fullName: string;
  role: string;
  storeId?: string;
  isActive?: boolean;
  lastLoginAt?: Date;
  createdAt?: Date;
  updatedAt?: Date;
}

export interface MetricDTO {
  id?: string;
  storeId: string;
  zoneId?: string;
  metricType: string;
  value: number;
  timestamp: Date | string;
  metadata?: any;
  createdAt?: Date;
}
