import React from 'react';
import { Hero } from '@/components/product/Hero';
import { LiveDemo } from '@/components/product/LiveDemo';
import { ModelPipeline } from '@/components/product/ModelPipeline';
import { ZoneMap } from '@/components/product/ZoneMap';
import { RetailIntelligence } from '@/components/product/RetailIntelligence';
import { ArchitectureDiagram } from '@/components/product/ArchitectureDiagram';
import { PrivacySection } from '@/components/product/PrivacySection';
import { BusinessModel } from '@/components/product/BusinessModel';

export default function Home() {
  return (
    <div className="flex flex-col">
      <Hero />
      <LiveDemo />
      <ModelPipeline />
      <ZoneMap />
      <RetailIntelligence />
      <ArchitectureDiagram />
      <PrivacySection />
      <BusinessModel />
    </div>
  );
}
