import React, { useState, useEffect } from 'react';
import { Calendar } from '@/components/ui/calendar';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Clock, CheckCircle, Loader2, AlertCircle } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface TimeSlot {
  start_time: string;
  end_time: string;
  duration_minutes: number;
  available: boolean;
}

interface AppointmentCalendarProps {
  appointmentType: string;
  onSlotSelected: (startTime: string, endTime: string) => void;
  selectedSlot?: { startTime: string; endTime: string };
}

export const AppointmentCalendar: React.FC<AppointmentCalendarProps> = ({
  appointmentType,
  onSlotSelected,
  selectedSlot,
}) => {
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(new Date());
  const [availableSlots, setAvailableSlots] = useState<TimeSlot[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    if (selectedDate) {
      fetchAvailability(selectedDate);
    }
  }, [selectedDate]);

  const fetchAvailability = async (date: Date) => {
    setLoading(true);
    setError(null);
    try {
      const dateStr = date.toISOString().split('T')[0]; // YYYY-MM-DD
      const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/appointments/availability?date=${dateStr}&duration=60&timezone=${encodeURIComponent(tz)}`
      );

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to fetch availability: ${errorText || response.statusText}`);
      }

      const data = await response.json();
      if (!data.success) {
        throw new Error(data.message || 'Failed to fetch availability');
      }
      setAvailableSlots(data.slots || []);
    } catch (error: any) {
      console.error('Error fetching availability:', error);
      const errorMessage = error.message || 'Failed to load available time slots. Please try again.';
      setError(errorMessage);
      toast({
        title: 'Error',
        description: errorMessage,
        variant: 'destructive',
      });
      setAvailableSlots([]);
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  };

  const isSlotSelected = (slot: TimeSlot) => {
    return selectedSlot?.startTime === slot.start_time && selectedSlot?.endTime === slot.end_time;
  };

  const isPastDate = (date: Date) => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return date < today;
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Select Date & Time</CardTitle>
          <CardDescription>
            Choose your preferred date and time slot for your {appointmentType.replace('_', ' ')}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 gap-6">
            {/* Calendar */}
            <div>
              <h3 className="font-semibold mb-4">Select a Date</h3>
              <Calendar
                mode="single"
                selected={selectedDate}
                onSelect={setSelectedDate}
                disabled={(date) => isPastDate(date)}
                className="rounded-md border"
              />
              <p className="text-sm text-muted-foreground mt-2">
                <Clock className="inline w-4 h-4 mr-1" />
                All times shown in your local timezone
              </p>
            </div>

            {/* Time Slots */}
            <div>
              <h3 className="font-semibold mb-4">
                Available Times {selectedDate && `- ${selectedDate.toLocaleDateString()}`}
              </h3>
              
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-primary" />
                </div>
              ) : error ? (
                <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                  <AlertCircle className="h-12 w-12 text-destructive mb-4" />
                  <p className="text-center mb-2">Failed to load available time slots</p>
                  <p className="text-sm text-center">{error}</p>
                  <Button 
                    variant="outline" 
                    className="mt-4"
                    onClick={() => selectedDate && fetchAvailability(selectedDate)}
                  >
                    Retry
                  </Button>
                </div>
              ) : availableSlots.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  <p>No available slots for this date.</p>
                  <p className="text-sm mt-2">Please select another date.</p>
                </div>
              ) : (
                <div className="grid gap-2 max-h-[400px] overflow-y-auto pr-2">
                  {availableSlots.map((slot, index) => (
                    <Button
                      key={index}
                      variant={isSlotSelected(slot) ? 'default' : 'outline'}
                      className={`justify-between h-auto py-3 ${
                        isSlotSelected(slot) ? 'ring-2 ring-primary' : ''
                      }`}
                      onClick={() => onSlotSelected(slot.start_time, slot.end_time)}
                    >
                      <span className="flex items-center gap-2">
                        <Clock className="w-4 h-4" />
                        {formatTime(slot.start_time)}
                      </span>
                      {isSlotSelected(slot) && (
                        <CheckCircle className="w-4 h-4" />
                      )}
                    </Button>
                  ))}
                </div>
              )}
              
              {selectedSlot && (
                <div className="mt-4 p-4 bg-primary/10 rounded-lg">
                  <p className="text-sm font-semibold mb-1">Selected Time:</p>
                  <p className="text-sm">
                    {formatTime(selectedSlot.startTime)} - {formatTime(selectedSlot.endTime)}
                  </p>
                  <Badge className="mt-2">60 minutes</Badge>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};