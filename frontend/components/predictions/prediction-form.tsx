'use client';

import { useState } from 'react';
import type { PredictionInput } from '@/lib/predictions';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface PredictionFormProps {
  onSubmit: (input: PredictionInput) => Promise<void>;
  isSubmitting: boolean;
  disabled?: boolean;
}

const defaultValues: PredictionInput = {
  gender: 'Male',
  SeniorCitizen: 0,
  Partner: 'No',
  Dependents: 'No',
  tenure: 1,
  PhoneService: 'Yes',
  MultipleLines: 'No',
  InternetService: 'DSL',
  OnlineSecurity: 'No',
  OnlineBackup: 'No',
  DeviceProtection: 'No',
  TechSupport: 'No',
  StreamingTV: 'No',
  StreamingMovies: 'No',
  Contract: 'Month-to-month',
  PaperlessBilling: 'No',
  PaymentMethod: 'Electronic check',
  MonthlyCharges: 50.0,
  TotalCharges: 50.0,
};

function FormSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <h3 className="text-sm font-semibold text-foreground uppercase tracking-wide">{title}</h3>
        <Separator className="flex-1" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {children}
      </div>
    </div>
  );
}

function SelectField({
  label,
  value,
  onChange,
  options,
  disabled,
}: {
  label: string;
  value: string | number;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
  disabled?: boolean;
}) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      <Select value={String(value)} onValueChange={onChange} disabled={disabled}>
        <SelectTrigger>
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {options.map((opt) => (
            <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}

function NumberField({
  label,
  value,
  onChange,
  min,
  max,
  step,
  error,
  disabled,
  className,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  min: number;
  max: number;
  step?: number;
  error?: string;
  disabled?: boolean;
  className?: string;
}) {
  return (
    <div className={cn('space-y-2', className)}>
      <Label>{label}</Label>
      <Input
        type="number"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value) || 0)}
        disabled={disabled}
        className={error ? 'border-destructive' : ''}
      />
      {error && <p className="text-xs text-destructive mt-1">{error}</p>}
    </div>
  );
}

const YES_NO = [{ value: 'Yes', label: 'Yes' }, { value: 'No', label: 'No' }];
const YES_NO_NS = [...YES_NO, { value: 'No internet service', label: 'No internet service' }];
const YES_NO_NP = [...YES_NO, { value: 'No phone service', label: 'No phone service' }];

export default function PredictionForm({ onSubmit, isSubmitting, disabled = false }: PredictionFormProps) {
  const [formData, setFormData] = useState<PredictionInput>(defaultValues);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  const handleInputChange = <K extends keyof PredictionInput>(field: K, value: PredictionInput[K]) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (validationErrors[field]) {
      setValidationErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};
    if (formData.tenure < 0 || formData.tenure > 100) errors.tenure = 'Tenure must be between 0 and 100 months';
    if (formData.MonthlyCharges < 0 || formData.MonthlyCharges > 1000) errors.MonthlyCharges = 'Monthly charges must be between $0 and $1000';
    if (formData.TotalCharges < 0 || formData.TotalCharges > 10000) errors.TotalCharges = 'Total charges must be between $0 and $10,000';
    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;
    await onSubmit(formData);
  };

  const isDisabled = disabled || isSubmitting;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Customer Information</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-8">
          <FormSection title="Demographics">
            <SelectField label="Gender" value={formData.gender} onChange={(v) => handleInputChange('gender', v as 'Male' | 'Female')} options={[{ value: 'Male', label: 'Male' }, { value: 'Female', label: 'Female' }]} disabled={isDisabled} />
            <SelectField label="Senior Citizen" value={formData.SeniorCitizen} onChange={(v) => handleInputChange('SeniorCitizen', parseInt(v) as 0 | 1)} options={[{ value: '0', label: 'No' }, { value: '1', label: 'Yes' }]} disabled={isDisabled} />
            <SelectField label="Partner" value={formData.Partner} onChange={(v) => handleInputChange('Partner', v as 'Yes' | 'No')} options={YES_NO} disabled={isDisabled} />
            <SelectField label="Dependents" value={formData.Dependents} onChange={(v) => handleInputChange('Dependents', v as 'Yes' | 'No')} options={YES_NO} disabled={isDisabled} />
            <NumberField label="Tenure (months)" value={formData.tenure} onChange={(v) => handleInputChange('tenure', v)} min={0} max={100} error={validationErrors.tenure} disabled={isDisabled} className="md:col-span-2" />
          </FormSection>

          <FormSection title="Phone Services">
            <SelectField label="Phone Service" value={formData.PhoneService} onChange={(v) => handleInputChange('PhoneService', v as 'Yes' | 'No')} options={YES_NO} disabled={isDisabled} />
            <SelectField label="Multiple Lines" value={formData.MultipleLines} onChange={(v) => handleInputChange('MultipleLines', v as 'Yes' | 'No' | 'No phone service')} options={YES_NO_NP} disabled={isDisabled} />
          </FormSection>

          <FormSection title="Internet Services">
            <div className="space-y-2 md:col-span-2">
              <Label>Internet Service</Label>
              <Select value={formData.InternetService} onValueChange={(v: string) => handleInputChange('InternetService', v as 'DSL' | 'Fiber optic' | 'No')} disabled={isDisabled}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="DSL">DSL</SelectItem>
                  <SelectItem value="Fiber optic">Fiber optic</SelectItem>
                  <SelectItem value="No">No</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <SelectField label="Online Security" value={formData.OnlineSecurity} onChange={(v) => handleInputChange('OnlineSecurity', v as 'Yes' | 'No' | 'No internet service')} options={YES_NO_NS} disabled={isDisabled} />
            <SelectField label="Online Backup" value={formData.OnlineBackup} onChange={(v) => handleInputChange('OnlineBackup', v as 'Yes' | 'No' | 'No internet service')} options={YES_NO_NS} disabled={isDisabled} />
            <SelectField label="Device Protection" value={formData.DeviceProtection} onChange={(v) => handleInputChange('DeviceProtection', v as 'Yes' | 'No' | 'No internet service')} options={YES_NO_NS} disabled={isDisabled} />
            <SelectField label="Tech Support" value={formData.TechSupport} onChange={(v) => handleInputChange('TechSupport', v as 'Yes' | 'No' | 'No internet service')} options={YES_NO_NS} disabled={isDisabled} />
            <SelectField label="Streaming TV" value={formData.StreamingTV} onChange={(v) => handleInputChange('StreamingTV', v as 'Yes' | 'No' | 'No internet service')} options={YES_NO_NS} disabled={isDisabled} />
            <SelectField label="Streaming Movies" value={formData.StreamingMovies} onChange={(v) => handleInputChange('StreamingMovies', v as 'Yes' | 'No' | 'No internet service')} options={YES_NO_NS} disabled={isDisabled} />
          </FormSection>

          <FormSection title="Billing Information">
            <div className="space-y-2">
              <Label>Contract</Label>
              <Select value={formData.Contract} onValueChange={(v: string) => handleInputChange('Contract', v as 'Month-to-month' | 'One year' | 'Two year')} disabled={isDisabled}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="Month-to-month">Month-to-month</SelectItem>
                  <SelectItem value="One year">One year</SelectItem>
                  <SelectItem value="Two year">Two year</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <SelectField label="Paperless Billing" value={formData.PaperlessBilling} onChange={(v) => handleInputChange('PaperlessBilling', v as 'Yes' | 'No')} options={YES_NO} disabled={isDisabled} />
            <div className="space-y-2 md:col-span-2">
              <Label>Payment Method</Label>
              <Select value={formData.PaymentMethod} onValueChange={(v: string) => handleInputChange('PaymentMethod', v as PredictionInput['PaymentMethod'])} disabled={isDisabled}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="Electronic check">Electronic check</SelectItem>
                  <SelectItem value="Mailed check">Mailed check</SelectItem>
                  <SelectItem value="Bank transfer (automatic)">Bank transfer (automatic)</SelectItem>
                  <SelectItem value="Credit card (automatic)">Credit card (automatic)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <NumberField label="Monthly Charges ($)" value={formData.MonthlyCharges} onChange={(v) => handleInputChange('MonthlyCharges', v)} min={0} max={1000} step={0.01} error={validationErrors.MonthlyCharges} disabled={isDisabled} />
            <NumberField label="Total Charges ($)" value={formData.TotalCharges} onChange={(v) => handleInputChange('TotalCharges', v)} min={0} max={10000} step={0.01} error={validationErrors.TotalCharges} disabled={isDisabled} />
          </FormSection>

          <div className="flex justify-end gap-3 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => { setFormData(defaultValues); setValidationErrors({}); }}
              disabled={isDisabled}
            >
              Reset
            </Button>
            <Button type="submit" disabled={isDisabled}>
              {isSubmitting ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Predicting...</> : 'Predict Churn'}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
