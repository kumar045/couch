from rest_framework import serializers

from stream_api.models import Stream




class StreamSerializer(serializers.ModelSerializer):
   class Meta:
        model = Stream
        fields = '__all__'
        
   

    
    
   

