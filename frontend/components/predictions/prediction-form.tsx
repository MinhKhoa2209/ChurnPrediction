/**
 * Prediction Form Component
 * Requirement 12.1: Form accepting all customer feature inputs
 * Requirement 12.2: Validate all required fields are present
 * 
 * Provides a comprehensive form for entering customer data based on the
 * Telco Customer Churn dataset schema.
 */

'use client';

import { useState } from 'react';
import type { PredictionInput } from '@/lib/predictions';

interface PredictionFormProps {
  onSubmit: (input: PredictionInput) => Promise<void>;
  isSubmitting: boolean;
  disabled?: boolean;
}

export default function PredictionForm({
  onSubmit,
  isSubmitting,
  disabled = false,
}: PredictionFormProps) {
  const [formData, setFormData] = useState<PredictionInput>({
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
  });

  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  const handleInputChange = (field: keyof PredictionInput, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    // Clear validation error for this field
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

    // Validate numeric fields
    if (formData.tenure < 0 || formData.tenure > 100) {
      errors.tenure = 'Tenure must be between 0 and 100 months';
    }
    if (formData.MonthlyCharges < 0 || formData.MonthlyCharges > 1000) {
      errors.MonthlyCharges = 'Monthly charges must be between $0 and $1000';
    }
    if (formData.TotalCharges < 0 || formData.TotalCharges > 10000) {
      errors.TotalCharges = 'Total charges must be between $0 and $10,000';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    await onSubmit(formData);
  };

  const handleReset = () => {
    setFormData({
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
    });
    setValidationErrors({});
  };

  return (
    <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
      <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">
        Customer Information
      </h2>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Demographics Section */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Demographics
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Gender */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Gender
              </label>
              <select
                value={formData.gender}
                onChange={(e) => handleInputChange('gender', e.target.value as 'Male' | 'Female')}
                disabled={disabled || isSubmitting}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
              >
                <option value="Male">Male</option>
                <option value="Female">Female</option>
              </select>
            </div>

            {/* Senior Citizen */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Senior Citizen
              </label>
              <select
                value={formData.SeniorCitizen}
                onChange={(e) => handleInputChange('SeniorCitizen', parseInt(e.target.value) as 0 | 1)}
                disabled={disabled || isSubmitting}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
              >
                <option value={0}>No</option>
                <option value={1}>Yes</option>
              </select>
            </div>

            {/* Partner */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Partner
              </label>
              <select
                value={formData.Partner}
                onChange={(e) => handleInputChange('Partner', e.target.value as 'Yes' | 'No')}
                disabled={disabled || isSubmitting}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
              >
                <option value="Yes">Yes</option>
                <option value="No">No</option>
              </select>
            </div>

            {/* Dependents */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Dependents
              </label>
              <select
                value={formData.Dependents}
                onChange={(e) => handleInputChange('Dependents', e.target.value as 'Yes' | 'No')}
                disabled={disabled || isSubmitting}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
              >
                <option value="Yes">Yes</option>
                <option value="No">No</option>
              </select>
            </div>

            {/* Tenure */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Tenure (months)
              </label>
              <input
                type="number"
                min="0"
                max="100"
                value={formData.tenure}
                onChange={(e) => handleInputChange('tenure', parseInt(e.target.value) || 0)}
                disabled={disabled || isSubmitting}
                className={`w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50 ${
                  validationErrors.tenure ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
                }`}
              />
              {validationErrors.tenure && (
                <p className="text-sm text-red-600 dark:text-red-400 mt-1">{validationErrors.tenure}</p>
              )}
            </div>
          </div>
        </div>

        {/* Phone Services Section */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Phone Services
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Phone Service */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Phone Service
              </label>
              <select
                value={formData.PhoneService}
                onChange={(e) => handleInputChange('PhoneService', e.target.value as 'Yes' | 'No')}
                disabled={disabled || isSubmitting}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
              >
                <option value="Yes">Yes</option>
                <option value="No">No</option>
              </select>
            </div>

            {/* Multiple Lines */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Multiple Lines
              </label>
              <select
                value={formData.MultipleLines}
                onChange={(e) => handleInputChange('MultipleLines', e.target.value as 'Yes' | 'No' | 'No phone service')}
                disabled={disabled || isSubmitting}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
              >
                <option value="Yes">Yes</option>
                <option value="No">No</option>
                <option value="No phone service">No phone service</option>
              </select>
            </div>
          </div>
        </div>

        {/* Internet Services Section */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Internet Services
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Internet Service */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Internet Service
              </label>
              <select
                value={formData.InternetService}
                onChange={(e) => handleInputChange('InternetService', e.target.value as 'DSL' | 'Fiber optic' | 'No')}
                disabled={disabled || isSubmitting}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
              >
                <option value="DSL">DSL</option>
                <option value="Fiber optic">Fiber optic</option>
                <option value="No">No</option>
              </select>
            </div>

            {/* Online Security */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Online Security
              </label>
              <select
                value={formData.OnlineSecurity}
                onChange={(e) => handleInputChange('OnlineSecurity', e.target.value as 'Yes' | 'No' | 'No internet service')}
                disabled={disabled || isSubmitting}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
              >
                <option value="Yes">Yes</option>
                <option value="No">No</option>
                <option value="No internet service">No internet service</option>
              </select>
            </div>

            {/* Online Backup */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Online Backup
              </label>
              <select
                value={formData.OnlineBackup}
                onChange={(e) => handleInputChange('OnlineBackup', e.target.value as 'Yes' | 'No' | 'No internet service')}
                disabled={disabled || isSubmitting}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
              >
                <option value="Yes">Yes</option>
                <option value="No">No</option>
                <option value="No internet service">No internet service</option>
              </select>
            </div>

            {/* Device Protection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Device Protection
              </label>
              <select
                value={formData.DeviceProtection}
                onChange={(e) => handleInputChange('DeviceProtection', e.target.value as 'Yes' | 'No' | 'No internet service')}
                disabled={disabled || isSubmitting}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
              >
                <option value="Yes">Yes</option>
                <option value="No">No</option>
                <option value="No internet service">No internet service</option>
              </select>
            </div>

            {/* Tech Support */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Tech Support
              </label>
              <select
                value={formData.TechSupport}
                onChange={(e) => handleInputChange('TechSupport', e.target.value as 'Yes' | 'No' | 'No internet service')}
                disabled={disabled || isSubmitting}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
              >
                <option value="Yes">Yes</option>
                <option value="No">No</option>
                <option value="No internet service">No internet service</option>
              </select>
            </div>

            {/* Streaming TV */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Streaming TV
              </label>
              <select
                value={formData.StreamingTV}
                onChange={(e) => handleInputChange('StreamingTV', e.target.value as 'Yes' | 'No' | 'No internet service')}
                disabled={disabled || isSubmitting}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
              >
                <option value="Yes">Yes</option>
                <option value="No">No</option>
                <option value="No internet service">No internet service</option>
              </select>
            </div>

            {/* Streaming Movies */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Streaming Movies
              </label>
              <select
                value={formData.StreamingMovies}
                onChange={(e) => handleInputChange('StreamingMovies', e.target.value as 'Yes' | 'No' | 'No internet service')}
                disabled={disabled || isSubmitting}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
              >
                <option value="Yes">Yes</option>
                <option value="No">No</option>
                <option value="No internet service">No internet service</option>
              </select>
            </div>
          </div>
        </div>

        {/* Billing Section */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Billing Information
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Contract */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Contract
              </label>
              <select
                value={formData.Contract}
                onChange={(e) => handleInputChange('Contract', e.target.value as 'Month-to-month' | 'One year' | 'Two year')}
                disabled={disabled || isSubmitting}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
              >
                <option value="Month-to-month">Month-to-month</option>
                <option value="One year">One year</option>
                <option value="Two year">Two year</option>
              </select>
            </div>

            {/* Paperless Billing */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Paperless Billing
              </label>
              <select
                value={formData.PaperlessBilling}
                onChange={(e) => handleInputChange('PaperlessBilling', e.target.value as 'Yes' | 'No')}
                disabled={disabled || isSubmitting}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
              >
                <option value="Yes">Yes</option>
                <option value="No">No</option>
              </select>
            </div>

            {/* Payment Method */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Payment Method
              </label>
              <select
                value={formData.PaymentMethod}
                onChange={(e) => handleInputChange('PaymentMethod', e.target.value as PredictionInput['PaymentMethod'])}
                disabled={disabled || isSubmitting}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
              >
                <option value="Electronic check">Electronic check</option>
                <option value="Mailed check">Mailed check</option>
                <option value="Bank transfer (automatic)">Bank transfer (automatic)</option>
                <option value="Credit card (automatic)">Credit card (automatic)</option>
              </select>
            </div>

            {/* Monthly Charges */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Monthly Charges ($)
              </label>
              <input
                type="number"
                min="0"
                max="1000"
                step="0.01"
                value={formData.MonthlyCharges}
                onChange={(e) => handleInputChange('MonthlyCharges', parseFloat(e.target.value) || 0)}
                disabled={disabled || isSubmitting}
                className={`w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50 ${
                  validationErrors.MonthlyCharges ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
                }`}
              />
              {validationErrors.MonthlyCharges && (
                <p className="text-sm text-red-600 dark:text-red-400 mt-1">{validationErrors.MonthlyCharges}</p>
              )}
            </div>

            {/* Total Charges */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Total Charges ($)
              </label>
              <input
                type="number"
                min="0"
                max="10000"
                step="0.01"
                value={formData.TotalCharges}
                onChange={(e) => handleInputChange('TotalCharges', parseFloat(e.target.value) || 0)}
                disabled={disabled || isSubmitting}
                className={`w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50 ${
                  validationErrors.TotalCharges ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
                }`}
              />
              {validationErrors.TotalCharges && (
                <p className="text-sm text-red-600 dark:text-red-400 mt-1">{validationErrors.TotalCharges}</p>
              )}
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
          <button
            type="button"
            onClick={handleReset}
            disabled={disabled || isSubmitting}
            className="px-6 py-2 text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Reset
          </button>
          <button
            type="submit"
            disabled={disabled || isSubmitting}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center"
          >
            {isSubmitting ? (
              <>
                <svg
                  className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                Predicting...
              </>
            ) : (
              'Predict Churn'
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
